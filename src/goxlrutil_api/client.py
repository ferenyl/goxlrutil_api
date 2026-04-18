"""GoXLRClient – high-level async API for the GoXLR Utility daemon."""

from __future__ import annotations

import logging
from typing import Any

from goxlrutil_api.exceptions import CommandError
from goxlrutil_api.protocol.commands import DaemonRequest, GoXLRCommand
from goxlrutil_api.protocol.responses import DaemonResponse, DaemonStatus
from goxlrutil_api.protocol.types import ChannelName, FaderName, MuteState
from goxlrutil_api.state import DaemonState
from goxlrutil_api.transport.base import Transport

_log = logging.getLogger(__name__)


class GoXLRClient:
    """
    Async client for the GoXLR Utility daemon.

    Usage::

        async with GoXLRClient(transport) as client:
            status = await client.get_status()
            serial = next(iter(status.mixers))
            await client.set_volume(serial, ChannelName.Mic, 200)
    """

    def __init__(self, transport: Transport) -> None:
        self._transport = transport
        self._state = DaemonState()

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    async def __aenter__(self) -> GoXLRClient:
        await self._transport.connect()
        await self._transport.subscribe(self._on_patch)
        return self

    async def __aexit__(self, *_: object) -> None:
        await self._transport.disconnect()

    # ------------------------------------------------------------------
    # Core methods
    # ------------------------------------------------------------------

    async def ping(self) -> bool:
        """Return True if the daemon responds to a ping."""
        resp = await self._transport.send(DaemonRequest.ping())
        return resp.ok

    async def get_status(self) -> DaemonStatus:
        """Fetch full daemon status and update internal state cache."""
        resp = await self._send_checked(DaemonRequest.get_status())
        if resp.status is not None:
            self._state.update(resp.status)
        return self._state.status

    async def get_mic_level(self, serial: str) -> float:
        """Return the current microphone level (0.0–1.0) for the given mixer."""
        resp = await self._send_checked(DaemonRequest.get_mic_level(serial))
        if resp.mic_level is None:
            return 0.0
        return resp.mic_level

    async def command(self, serial: str, cmd: GoXLRCommand) -> None:
        """Send a GoXLR command to a specific mixer."""
        await self._send_checked(DaemonRequest.command(serial, cmd))

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------

    async def set_volume(self, serial: str, channel: ChannelName, volume: int) -> None:
        """Set channel volume (0–255)."""
        from goxlrutil_api.protocol.commands import GoXLRCommand
        await self.command(serial, GoXLRCommand.set_volume(channel, volume))

    async def set_fader_mute_state(self, serial: str, fader: FaderName, state: MuteState) -> None:
        from goxlrutil_api.protocol.commands import GoXLRCommand  # noqa: PLC0415
        await self.command(serial, GoXLRCommand.set_fader_mute_state(fader, state))

    async def set_fx_enabled(self, serial: str, enabled: bool) -> None:
        from goxlrutil_api.protocol.commands import GoXLRCommand  # noqa: PLC0415
        await self.command(serial, GoXLRCommand.set_fx_enabled(enabled))

    # ------------------------------------------------------------------
    # State access
    # ------------------------------------------------------------------

    @property
    def state(self) -> DaemonState:
        """Access the cached daemon state directly."""
        return self._state

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    async def _send_checked(self, request: DaemonRequest) -> DaemonResponse:
        resp = await self._transport.send(request)
        if resp.error is not None:
            raise CommandError(resp.error)
        return resp

    async def _on_patch(self, ops: list[Any]) -> None:
        """Called by the transport when a live Patch event arrives."""
        self._state.apply_patch(ops)
