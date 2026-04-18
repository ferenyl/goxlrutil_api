"""Unix socket transport.

Frame format (identical to Rust LengthDelimitedCodec defaults):
  4 bytes  big-endian uint32  – payload length in bytes
  N bytes  UTF-8 JSON         – serialised DaemonRequest / DaemonResponse
"""

from __future__ import annotations

import asyncio
import json
import struct
from pathlib import Path

from goxlrutil_api.exceptions import ConnectionError, ProtocolError
from goxlrutil_api.protocol.commands import DaemonRequest
from goxlrutil_api.protocol.responses import DaemonResponse
from goxlrutil_api.transport.base import Transport

_HEADER = struct.Struct(">I")  # big-endian uint32
DEFAULT_SOCKET_PATH = Path("/tmp/goxlr.socket")


class UnixSocketTransport(Transport):
    """Communicate with the local GoXLR daemon via Unix domain socket."""

    def __init__(self, socket_path: Path = DEFAULT_SOCKET_PATH) -> None:
        self._path = socket_path
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None

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

    async def disconnect(self) -> None:
        if self._writer is not None:
            try:
                self._writer.close()
                await self._writer.wait_closed()
            except OSError:
                pass
            self._writer = None
            self._reader = None

    async def send(self, request: DaemonRequest) -> DaemonResponse:
        await self._write_frame(request.to_json().encode())
        raw = await self._read_frame()
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ProtocolError(f"Invalid JSON from daemon: {exc}") from exc
        return DaemonResponse.from_dict(data)

    # ------------------------------------------------------------------
    # Internal framing helpers
    # ------------------------------------------------------------------

    async def _write_frame(self, payload: bytes) -> None:
        if self._writer is None:
            raise ConnectionError("Not connected")
        header = _HEADER.pack(len(payload))
        self._writer.write(header + payload)
        await self._writer.drain()

    async def _read_frame(self) -> bytes:
        if self._reader is None:
            raise ConnectionError("Not connected")
        header = await self._reader.readexactly(_HEADER.size)
        length = _HEADER.unpack(header)[0]
        return await self._reader.readexactly(length)
