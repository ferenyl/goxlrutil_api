"""HTTP transport.

Sends DaemonRequest as JSON to POST /api/command and returns DaemonResponse.
Suitable for both local and remote GoXLR daemons (when network access is enabled).
"""

from __future__ import annotations

import httpx

from goxlrutil_api.exceptions import ConnectionError, ProtocolError
from goxlrutil_api.protocol.commands import DaemonRequest
from goxlrutil_api.protocol.responses import DaemonResponse
from goxlrutil_api.transport.base import Transport

DEFAULT_URL = "http://localhost:14564/api/command"


class HttpTransport(Transport):
    """Communicate with the GoXLR daemon via HTTP POST."""

    def __init__(self, url: str = DEFAULT_URL, timeout: float = 10.0) -> None:
        self._url = url
        self._timeout = timeout
        self._client: httpx.AsyncClient | None = None

    # ------------------------------------------------------------------
    # Transport interface
    # ------------------------------------------------------------------

    async def connect(self) -> None:
        self._client = httpx.AsyncClient(timeout=self._timeout)

    async def disconnect(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def send(self, request: DaemonRequest) -> DaemonResponse:
        if self._client is None:
            raise ConnectionError("HttpTransport not connected – call connect() first")
        payload = request.to_json()
        try:
            resp = await self._client.post(
                self._url,
                content=payload,
                headers={"Content-Type": "application/json"},
            )
            resp.raise_for_status()
        except httpx.ConnectError as exc:
            raise ConnectionError(f"Cannot reach GoXLR daemon at {self._url}: {exc}") from exc
        except httpx.HTTPStatusError as exc:
            raise ProtocolError(f"HTTP {exc.response.status_code} from daemon") from exc

        try:
            data = resp.json()
        except Exception as exc:
            raise ProtocolError(f"Non-JSON response from daemon: {exc}") from exc

        return DaemonResponse.from_dict(data)
