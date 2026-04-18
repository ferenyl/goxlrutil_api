"""Sync wrappers around the async GoXLRClient."""

from __future__ import annotations

import asyncio
from typing import Any

from goxlrutil_api.client import GoXLRClient
from goxlrutil_api.protocol.commands import GoXLRCommand
from goxlrutil_api.protocol.responses import DaemonStatus
from goxlrutil_api.protocol.types import ChannelName
from goxlrutil_api.transport.base import Transport


def run_sync(coro: Any) -> Any:  # noqa: ANN401
    """Run an async coroutine synchronously, creating an event loop if needed."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop is not None and loop.is_running():
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(asyncio.run, coro)
            return future.result()
    return asyncio.run(coro)


class GoXLRClientSync:
    """Synchronous wrapper around GoXLRClient for non-async contexts."""

    def __init__(self, transport: Transport) -> None:
        self._async = GoXLRClient(transport)
        self._transport = transport

    def __enter__(self) -> GoXLRClientSync:
        run_sync(self._async.__aenter__())
        return self

    def __exit__(self, *_: object) -> None:
        run_sync(self._async.__aexit__(None, None, None))

    def ping(self) -> bool:
        return run_sync(self._async.ping())

    def get_status(self) -> DaemonStatus:
        return run_sync(self._async.get_status())

    def get_mic_level(self, serial: str) -> float:
        return run_sync(self._async.get_mic_level(serial))

    def command(self, serial: str, cmd: GoXLRCommand) -> None:
        run_sync(self._async.command(serial, cmd))

    def set_volume(self, serial: str, channel: ChannelName, volume: int) -> None:
        run_sync(self._async.set_volume(serial, channel, volume))

    def set_fx_enabled(self, serial: str, enabled: bool) -> None:
        run_sync(self._async.set_fx_enabled(serial, enabled))
