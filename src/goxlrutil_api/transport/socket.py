"""Unix socket transport.

Frame format (identical to Rust LengthDelimitedCodec defaults):
  4 bytes  big-endian uint32  – payload length in bytes
  N bytes  UTF-8 JSON         – serialised DaemonRequest / DaemonResponse

The daemon can push unsolicited Patch events over the same connection at any
time, so we run a background listener task (analogous to WebSocketTransport).
Responses to outgoing requests are matched FIFO via an asyncio.Queue of
pending futures.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
import struct
from pathlib import Path

from goxlrutil_api.exceptions import ConnectionError, ProtocolError
from goxlrutil_api.protocol.commands import DaemonRequest
from goxlrutil_api.protocol.responses import DaemonResponse
from goxlrutil_api.transport.base import PatchCallback, Transport

_log = logging.getLogger(__name__)
_HEADER = struct.Struct(">I")  # big-endian uint32
DEFAULT_SOCKET_PATH = Path("/tmp/goxlr.socket")


class UnixSocketTransport(Transport):
    """Communicate with the local GoXLR daemon via Unix domain socket."""

    def __init__(self, socket_path: Path = DEFAULT_SOCKET_PATH) -> None:
        self._path = socket_path
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None
        self._patch_callback: PatchCallback | None = None
        self._listener_task: asyncio.Task[None] | None = None
        # FIFO queue of futures waiting for the next non-patch response frame
        self._pending: asyncio.Queue[asyncio.Future[DaemonResponse]] = asyncio.Queue()

    # ------------------------------------------------------------------
    # Transport interface
    # ------------------------------------------------------------------

    async def connect(self) -> None:
        if not self._path.exists():
            raise ConnectionError(f"GoXLR socket not found: {self._path}")
        try:
            self._reader, self._writer = await asyncio.open_unix_connection(str(self._path))
        except OSError as exc:
            raise ConnectionError(f"Cannot connect to {self._path}: {exc}") from exc
        self._listener_task = asyncio.create_task(
            self._listen(), name="goxlr-socket-listener"
        )

    async def disconnect(self) -> None:
        if self._listener_task is not None:
            self._listener_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._listener_task
            self._listener_task = None
        if self._writer is not None:
            with contextlib.suppress(OSError):
                self._writer.close()
                await self._writer.wait_closed()
            self._writer = None
            self._reader = None

    async def send(self, request: DaemonRequest) -> DaemonResponse:
        if self._writer is None:
            raise ConnectionError("Not connected")
        future: asyncio.Future[DaemonResponse] = asyncio.get_running_loop().create_future()
        await self._pending.put(future)
        await self._write_frame(request.to_json().encode())
        try:
            return await asyncio.wait_for(asyncio.shield(future), timeout=10.0)
        except TimeoutError as exc:
            # Remove the stale future from the queue if possible
            future.cancel()
            raise ProtocolError("Timeout waiting for response from daemon") from exc

    async def subscribe(self, callback: PatchCallback) -> None:
        self._patch_callback = callback

    # ------------------------------------------------------------------
    # Internal: background listener
    # ------------------------------------------------------------------

    async def _listen(self) -> None:
        try:
            while True:
                frame = await self._read_frame()
                await self._handle_frame(frame)
        except asyncio.CancelledError:
            pass
        except asyncio.IncompleteReadError:
            _log.warning("GoXLR daemon closed the socket connection")
        except Exception as exc:
            _log.warning("Socket listener error: %s", exc)

    async def _handle_frame(self, raw: bytes) -> None:
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            _log.warning("Invalid JSON from daemon socket: %s", exc)
            return

        response = DaemonResponse.from_dict(data)

        if response.patch is not None:
            if self._patch_callback is not None:
                try:
                    await self._patch_callback(response.patch)
                except Exception as exc:
                    _log.warning("Patch callback raised: %s", exc)
        else:
            # This is a response to an outgoing request — resolve next pending future
            if not self._pending.empty():
                future = await self._pending.get()
                if not future.cancelled():
                    future.set_result(response)
            else:
                _log.debug("Received response frame with no pending request: %r", data)

    # ------------------------------------------------------------------
    # Internal: framing
    # ------------------------------------------------------------------

    async def _write_frame(self, payload: bytes) -> None:
        assert self._writer is not None
        self._writer.write(_HEADER.pack(len(payload)) + payload)
        await self._writer.drain()

    async def _read_frame(self) -> bytes:
        assert self._reader is not None
        header = await self._reader.readexactly(_HEADER.size)
        length = _HEADER.unpack(header)[0]
        return await self._reader.readexactly(length)

