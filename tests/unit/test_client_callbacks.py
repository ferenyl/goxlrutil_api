"""Tests for GoXLRClient on_state_update, on_connect, and on_disconnect callbacks."""

from __future__ import annotations

from typing import Any

import pytest

from goxlrutil_api.client import GoXLRClient
from goxlrutil_api.protocol.commands import DaemonRequest
from goxlrutil_api.protocol.responses import DaemonResponse, DaemonStatus
from goxlrutil_api.transport.base import (
    ConnectCallback,
    DisconnectCallback,
    PatchCallback,
    Transport,
)

# ---------------------------------------------------------------------------
# Stub transport with connect/disconnect hooks
# ---------------------------------------------------------------------------

class CallbackTransport(Transport):
    """Transport that exposes connect/disconnect callbacks for testing."""

    def __init__(self, status_raw: dict[str, Any]) -> None:
        self._status_raw = status_raw
        self._patch_cb: PatchCallback | None = None
        self._connect_cb: ConnectCallback | None = None
        self._disconnect_cb: DisconnectCallback | None = None

    async def connect(self) -> None:
        pass

    async def disconnect(self) -> None:
        pass

    async def send(self, request: DaemonRequest) -> DaemonResponse:
        return DaemonResponse(raw_status=self._status_raw)

    async def subscribe(self, callback: PatchCallback) -> None:
        self._patch_cb = callback

    async def subscribe_connect(self, callback: ConnectCallback) -> None:
        self._connect_cb = callback

    async def subscribe_disconnect(self, callback: DisconnectCallback) -> None:
        self._disconnect_cb = callback

    async def fire_patch(self, ops: list[Any]) -> None:
        if self._patch_cb is not None:
            await self._patch_cb(ops)

    async def fire_connect(self) -> None:
        if self._connect_cb is not None:
            await self._connect_cb()

    async def fire_disconnect(self) -> None:
        if self._disconnect_cb is not None:
            await self._disconnect_cb()


def _status_raw(volume: int = 128) -> dict[str, Any]:
    return {
        "config": {"daemon_version": "1.0.0", "http_settings": {}},
        "mixers": {
            "SER001": {
                "hardware": {"device_type": "Full", "colour_way": "Black"},
                "fader_status": {},
                "levels": {"volumes": {"Mic": volume}, "output_monitor": "Headphones"},
                "cough_button": {},
                "button_down": {},
                "router": {},
                "profile_name": "Default",
                "mic_profile_name": "MicDefault",
            }
        },
        "paths": {},
        "files": {},
    }


# ---------------------------------------------------------------------------
# on_state_update
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_on_state_update_called_on_patch() -> None:
    updates: list[DaemonStatus] = []

    async def on_update(status: DaemonStatus) -> None:
        updates.append(status)

    transport = CallbackTransport(_status_raw())
    async with GoXLRClient(transport, on_state_update=on_update) as client:
        await client.get_status()
        await transport.fire_patch(
            [{"op": "replace", "path": "/mixers/SER001/levels/volumes/Mic", "value": 200}]
        )

    assert len(updates) == 1
    assert updates[0].mixers["SER001"].levels.volumes["Mic"] == 200


@pytest.mark.asyncio
async def test_on_state_update_receives_full_status() -> None:
    """The callback receives the full DaemonStatus, not just the patch delta."""
    received: list[DaemonStatus] = []

    async def on_update(status: DaemonStatus) -> None:
        received.append(status)

    transport = CallbackTransport(_status_raw(volume=50))
    async with GoXLRClient(transport, on_state_update=on_update) as client:
        await client.get_status()
        await transport.fire_patch(
            [{"op": "replace", "path": "/mixers/SER001/levels/volumes/Mic", "value": 99}]
        )

    status = received[0]
    assert isinstance(status, DaemonStatus)
    # Other fields are still present (full status, not just diff)
    assert "SER001" in status.mixers


@pytest.mark.asyncio
async def test_on_state_update_not_called_without_patch() -> None:
    updates: list[DaemonStatus] = []

    async def on_update(status: DaemonStatus) -> None:
        updates.append(status)

    transport = CallbackTransport(_status_raw())
    async with GoXLRClient(transport, on_state_update=on_update) as client:
        await client.get_status()
        # No patch fired

    assert len(updates) == 0


@pytest.mark.asyncio
async def test_on_state_update_called_multiple_times() -> None:
    updates: list[int] = []

    async def on_update(status: DaemonStatus) -> None:
        updates.append(status.mixers["SER001"].levels.volumes.get("Mic", 0))

    transport = CallbackTransport(_status_raw())
    async with GoXLRClient(transport, on_state_update=on_update) as client:
        await client.get_status()
        await transport.fire_patch(
            [{"op": "replace", "path": "/mixers/SER001/levels/volumes/Mic", "value": 100}]
        )
        await transport.fire_patch(
            [{"op": "replace", "path": "/mixers/SER001/levels/volumes/Mic", "value": 200}]
        )

    assert updates == [100, 200]


# ---------------------------------------------------------------------------
# on_connect
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_on_connect_callback_called_on_reconnect() -> None:
    connect_calls: list[int] = []

    async def on_connect() -> None:
        connect_calls.append(1)

    transport = CallbackTransport(_status_raw())
    async with GoXLRClient(transport, on_connect=on_connect) as _:
        await transport.fire_connect()

    assert len(connect_calls) == 1


@pytest.mark.asyncio
async def test_on_connect_called_multiple_reconnects() -> None:
    connect_calls: list[int] = []

    async def on_connect() -> None:
        connect_calls.append(1)

    transport = CallbackTransport(_status_raw())
    async with GoXLRClient(transport, on_connect=on_connect) as _:
        await transport.fire_connect()
        await transport.fire_connect()

    assert len(connect_calls) == 2


@pytest.mark.asyncio
async def test_no_on_connect_does_not_crash() -> None:
    transport = CallbackTransport(_status_raw())
    async with GoXLRClient(transport) as _:
        await transport.fire_connect()  # should not raise


# ---------------------------------------------------------------------------
# on_disconnect
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_on_disconnect_callback_called() -> None:
    disconnect_calls: list[int] = []

    async def on_disconnect() -> None:
        disconnect_calls.append(1)

    transport = CallbackTransport(_status_raw())
    async with GoXLRClient(transport, on_disconnect=on_disconnect) as _:
        await transport.fire_disconnect()

    assert len(disconnect_calls) == 1


@pytest.mark.asyncio
async def test_on_disconnect_called_multiple_times() -> None:
    disconnect_calls: list[int] = []

    async def on_disconnect() -> None:
        disconnect_calls.append(1)

    transport = CallbackTransport(_status_raw())
    async with GoXLRClient(transport, on_disconnect=on_disconnect) as _:
        await transport.fire_disconnect()
        await transport.fire_disconnect()

    assert len(disconnect_calls) == 2


@pytest.mark.asyncio
async def test_no_on_disconnect_does_not_crash() -> None:
    transport = CallbackTransport(_status_raw())
    async with GoXLRClient(transport) as _:
        await transport.fire_disconnect()  # should not raise


# ---------------------------------------------------------------------------
# Combined: disconnect → reconnect → state update
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_full_lifecycle_callbacks() -> None:
    log: list[str] = []

    async def on_connect() -> None:
        log.append("connect")

    async def on_disconnect() -> None:
        log.append("disconnect")

    async def on_update(status: DaemonStatus) -> None:
        log.append("update")

    transport = CallbackTransport(_status_raw())
    async with GoXLRClient(
        transport,
        on_connect=on_connect,
        on_disconnect=on_disconnect,
        on_state_update=on_update,
    ) as client:
        await client.get_status()
        await transport.fire_disconnect()
        await transport.fire_connect()
        await transport.fire_patch(
            [{"op": "replace", "path": "/mixers/SER001/levels/volumes/Mic", "value": 99}]
        )

    assert "disconnect" in log
    assert "connect" in log
    assert "update" in log
    # disconnect should precede connect
    assert log.index("disconnect") < log.index("connect")
