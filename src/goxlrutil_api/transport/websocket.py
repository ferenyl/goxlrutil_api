"""WebSocket transport.

Sends DaemonRequest wrapped in {"id": <uint>, "data": <request>} and receives
DaemonResponse unwrapped from {"id": <uint>, "data": <response>}.

Also listens for unsolicited Patch events pushed by the daemon and calls
the registered patch callback.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
from typing import Any

import httpx
from httpx_ws import AsyncWebSocketSession, aconnect_ws

from goxlrutil_api.exceptions import ConnectionError, ProtocolError
from goxlrutil_api.protocol.commands import DaemonRequest
from goxlrutil_api.protocol.responses import DaemonResponse
from goxlrutil_api.transport.base import PatchCallback, Transport

_log = logging.getLogger(__name__)

DEFAULT_WS_URL = "ws://localhost:14564/api/websocket"


class WebSocketTransport(Transport):
    """
    Communicate with the GoXLR daemon over WebSocket.

    Supports both request/response and live patch-event subscriptions.
    """

    def __init__(self, url: str = DEFAULT_WS_URL, timeout: float = 10.0) -> None:
        self._url = url
        self._timeout = timeout
        self._ws: AsyncWebSocketSession | None = None
        self._ws_cm: Any | None = None  # context manager kept for proper cleanup
        self._http_client: httpx.AsyncClient | None = None
        self._next_id: int = 1
        self._pending: dict[int, asyncio.Future[DaemonResponse]] = {}
        self._patch_callback: PatchCallback | None = None
        self._listener_task: asyncio.Task[None] | None = None

    # ------------------------------------------------------------------
    # Transport interface
    # ------------------------------------------------------------------

    async def connect(self) -> None:
        self._http_client = httpx.AsyncClient(timeout=self._timeout)
        try:
            self._ws_cm = aconnect_ws(self._url, self._http_client)
            self._ws = await self._ws_cm.__aenter__()
        except Exception as exc:
            raise ConnectionError(f"WebSocket connection failed to {self._url}: {exc}") from exc
        self._listener_task = asyncio.create_task(self._listen(), name="goxlr-ws-listener")

    async def disconnect(self) -> None:
        if self._listener_task is not None:
            self._listener_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._listener_task
            self._listener_task = None
        if self._ws_cm is not None:
            with contextlib.suppress(Exception):
                await self._ws_cm.__aexit__(None, None, None)
            self._ws = None
            self._ws_cm = None
        if self._http_client is not None:
            await self._http_client.aclose()
            self._http_client = None

    async def send(self, request: DaemonRequest) -> DaemonResponse:
        if self._ws is None:
            raise ConnectionError("WebSocketTransport not connected")
        msg_id = self._next_id
        self._next_id += 1
        future: asyncio.Future[DaemonResponse] = asyncio.get_running_loop().create_future()
        self._pending[msg_id] = future
        envelope = {"id": msg_id, "data": request.to_dict()}
        await self._ws.send_text(json.dumps(envelope))
        try:
            return await asyncio.wait_for(future, timeout=self._timeout)
        except TimeoutError as exc:
            self._pending.pop(msg_id, None)
            raise ProtocolError(f"Timeout waiting for response id={msg_id}") from exc

    async def subscribe(self, callback: PatchCallback) -> None:
        """Register a callback that receives raw JSON Patch lists."""
        self._patch_callback = callback

    # ------------------------------------------------------------------
    # Internal listener
    # ------------------------------------------------------------------

    async def _listen(self) -> None:
        assert self._ws is not None
        try:
            while True:
                text = await self._ws.receive_text()
                await self._handle_message(text)
        except asyncio.CancelledError:
            pass
        except Exception as exc:
            _log.warning("WebSocket listener error: %s", exc)

    async def _handle_message(self, text: str) -> None:
        try:
            envelope = json.loads(text)
        except json.JSONDecodeError as exc:
            _log.warning("Invalid JSON from daemon WS: %s", exc)
            return

        msg_id = envelope.get("id")
        raw_data = envelope.get("data")
        response = DaemonResponse.from_dict(raw_data)

        if msg_id is not None and msg_id in self._pending:
            self._pending.pop(msg_id).set_result(response)
        elif response.patch is not None and self._patch_callback is not None:
            try:
                await self._patch_callback(response.patch)
            except Exception as exc:
                _log.warning("Patch callback raised: %s", exc)
        else:
            _log.debug("Unhandled WS message id=%s", msg_id)
