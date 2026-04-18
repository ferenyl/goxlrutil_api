"""WebSocket transport.

Sends DaemonRequest wrapped in {"id": <uint>, "data": <request>} and receives
DaemonResponse unwrapped from {"id": <uint>, "data": <response>}.

Also listens for unsolicited Patch events pushed by the daemon and calls
the registered patch callback.

Supports automatic reconnection with exponential backoff.
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
from goxlrutil_api.transport.base import (
    ConnectCallback,
    DisconnectCallback,
    PatchCallback,
    Transport,
)

_log = logging.getLogger(__name__)

DEFAULT_WS_URL = "ws://localhost:14564/api/websocket"


class WebSocketTransport(Transport):
    """
    Communicate with the GoXLR daemon over WebSocket.

    Supports both request/response and live patch-event subscriptions.
    Automatically reconnects if the connection drops (enabled by default).

    Parameters
    ----------
    url:
        WebSocket URL of the daemon.
    timeout:
        Request/connect timeout in seconds.
    reconnect:
        Enable automatic reconnection on connection loss.
    reconnect_delay:
        Initial delay between reconnect attempts (doubles on each failure,
        capped at ``max_reconnect_delay``).
    max_reconnect_delay:
        Upper bound on reconnect delay in seconds.
    """

    def __init__(
        self,
        url: str = DEFAULT_WS_URL,
        timeout: float = 10.0,
        reconnect: bool = True,
        reconnect_delay: float = 1.0,
        max_reconnect_delay: float = 60.0,
    ) -> None:
        self._url = url
        self._timeout = timeout
        self._reconnect_enabled = reconnect
        self._reconnect_delay = reconnect_delay
        self._max_reconnect_delay = max_reconnect_delay

        self._ws: AsyncWebSocketSession | None = None
        self._ws_cm: Any | None = None
        self._http_client: httpx.AsyncClient | None = None
        self._next_id: int = 1
        self._pending: dict[int, asyncio.Future[DaemonResponse]] = {}

        self._patch_callback: PatchCallback | None = None
        self._connect_callback: ConnectCallback | None = None
        self._disconnect_callback: DisconnectCallback | None = None

        self._listener_task: asyncio.Task[None] | None = None
        self._stopping: bool = False

    # ------------------------------------------------------------------
    # Transport interface
    # ------------------------------------------------------------------

    async def connect(self) -> None:
        self._stopping = False
        self._http_client = httpx.AsyncClient(timeout=self._timeout)
        await self._do_connect()
        self._listener_task = asyncio.create_task(
            self._listen_loop(), name="goxlr-ws-listener"
        )

    async def disconnect(self) -> None:
        self._stopping = True
        if self._listener_task is not None:
            self._listener_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._listener_task
            self._listener_task = None
        await self._close_ws()
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
        self._patch_callback = callback

    async def subscribe_connect(self, callback: ConnectCallback) -> None:
        self._connect_callback = callback

    async def subscribe_disconnect(self, callback: DisconnectCallback) -> None:
        self._disconnect_callback = callback

    # ------------------------------------------------------------------
    # Internal: connection helpers
    # ------------------------------------------------------------------

    async def _do_connect(self) -> None:
        """Open the WebSocket. Raises ConnectionError on failure."""
        try:
            self._ws_cm = aconnect_ws(self._url, self._http_client)
            self._ws = await self._ws_cm.__aenter__()
        except Exception as exc:
            raise ConnectionError(
                f"WebSocket connection failed to {self._url}: {exc}"
            ) from exc

    async def _close_ws(self) -> None:
        """Close current WebSocket session quietly."""
        if self._ws_cm is not None:
            with contextlib.suppress(Exception):
                await self._ws_cm.__aexit__(None, None, None)
            self._ws = None
            self._ws_cm = None

    def _fail_pending(self, exc: Exception) -> None:
        """Reject all in-flight request futures (called on unexpected disconnect)."""
        for future in self._pending.values():
            if not future.done():
                future.set_exception(
                    ConnectionError(f"Connection lost: {exc}")
                )
        self._pending.clear()

    # ------------------------------------------------------------------
    # Internal: listener / reconnect loop
    # ------------------------------------------------------------------

    async def _listen_loop(self) -> None:
        """Outer loop: receive messages; reconnect with backoff on failure."""
        while not self._stopping:
            try:
                await self._listen_once()
                # _listen_once returns only on intentional cancel
                return
            except asyncio.CancelledError:
                return
            except Exception as exc:
                if self._stopping:
                    return
                _log.warning("GoXLR WebSocket disconnected: %s", exc)
                self._fail_pending(exc)

                if self._disconnect_callback is not None:
                    with contextlib.suppress(Exception):
                        await self._disconnect_callback()

                if not self._reconnect_enabled:
                    return

                await self._close_ws()
                await self._backoff_reconnect()

                if self._stopping:
                    return

                if self._connect_callback is not None:
                    with contextlib.suppress(Exception):
                        await self._connect_callback()

    async def _listen_once(self) -> None:
        """Inner loop: receive and dispatch messages until the socket closes."""
        assert self._ws is not None
        while True:
            text = await self._ws.receive_text()
            await self._handle_message(text)

    async def _backoff_reconnect(self) -> None:
        """Try to reconnect repeatedly with exponential backoff."""
        delay = self._reconnect_delay
        while not self._stopping:
            _log.info("GoXLR WebSocket reconnecting in %.0f s…", delay)
            await asyncio.sleep(delay)
            if self._stopping:
                return
            try:
                await self._do_connect()
                _log.info("GoXLR WebSocket reconnected.")
                return
            except Exception as exc:
                _log.warning("Reconnect attempt failed: %s", exc)
                delay = min(delay * 2, self._max_reconnect_delay)

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
