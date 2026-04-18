"""Unit tests for button event detection in GoXLRClient."""

from __future__ import annotations

import asyncio
from typing import Any

import pytest

from goxlrutil_api.client import GoXLRClient
from goxlrutil_api.events import ButtonEvent, ButtonEventType
from goxlrutil_api.protocol.commands import DaemonRequest
from goxlrutil_api.protocol.responses import DaemonResponse
from goxlrutil_api.transport.base import PatchCallback, Transport


# ---------------------------------------------------------------------------
# Minimal stub transport
# ---------------------------------------------------------------------------

class StubTransport(Transport):
    """Transport that returns a canned response and records calls."""

    def __init__(self, response: DaemonResponse) -> None:
        self._response = response
        self._patch_cb: PatchCallback | None = None

    async def connect(self) -> None:
        pass

    async def disconnect(self) -> None:
        pass

    async def send(self, request: DaemonRequest) -> DaemonResponse:
        return self._response

    async def subscribe(self, callback: PatchCallback) -> None:  # noqa: B027
        self._patch_cb = callback

    async def push_patch(self, ops: list[Any]) -> None:
        """Simulate daemon pushing a patch event."""
        if self._patch_cb is not None:
            await self._patch_cb(ops)


def _make_status_raw(button_down: dict[str, bool]) -> dict[str, Any]:
    return {
        "config": {"daemon_version": "1.0.0", "http_settings": {}},
        "mixers": {
            "SER001": {
                "hardware": {"device_type": "Full", "colour_way": "Black"},
                "fader_status": {},
                "levels": {"volumes": {}, "output_monitor": "Headphones"},
                "cough_button": {},
                "button_down": button_down,
                "router": {},
                "profile_name": "",
                "mic_profile_name": "",
            }
        },
        "paths": {},
        "files": {},
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _status_response(button_down: dict[str, bool]) -> DaemonResponse:
    raw = _make_status_raw(button_down)
    return DaemonResponse(raw_status=raw)


def _patch_ops(button: str, value: bool) -> list[dict[str, Any]]:
    return [{"op": "replace", "path": f"/mixers/SER001/button_down/{button}", "value": value}]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_button_pressed_event() -> None:
    events: list[ButtonEvent] = []

    async def cb(e: ButtonEvent) -> None:
        events.append(e)

    transport = StubTransport(_status_response({"Bleep": False}))
    async with GoXLRClient(transport, on_button_event=cb) as client:
        await client.get_status()
        await transport.push_patch(_patch_ops("Bleep", True))

    assert len(events) == 1
    assert events[0].button == "Bleep"
    assert events[0].event_type == ButtonEventType.pressed
    assert events[0].held_seconds == 0.0


@pytest.mark.asyncio
async def test_button_released_event() -> None:
    events: list[ButtonEvent] = []

    async def cb(e: ButtonEvent) -> None:
        events.append(e)

    transport = StubTransport(_status_response({"Cough": False}))
    async with GoXLRClient(transport, on_button_event=cb) as client:
        await client.get_status()
        await transport.push_patch(_patch_ops("Cough", True))
        await transport.push_patch(_patch_ops("Cough", False))

    assert events[-1].button == "Cough"
    assert events[-1].event_type == ButtonEventType.released
    assert events[-1].held_seconds >= 0.0


@pytest.mark.asyncio
async def test_button_long_press_fires_after_threshold() -> None:
    events: list[ButtonEvent] = []

    async def cb(e: ButtonEvent) -> None:
        events.append(e)

    transport = StubTransport(_status_response({"Bleep": False}))
    async with GoXLRClient(transport, on_button_event=cb, long_press_threshold=0.05) as client:
        await client.get_status()
        await transport.push_patch(_patch_ops("Bleep", True))
        await asyncio.sleep(0.1)  # longer than threshold

    long_press_events = [e for e in events if e.event_type == ButtonEventType.long_pressed]
    assert len(long_press_events) == 1
    assert long_press_events[0].held_seconds >= 0.05


@pytest.mark.asyncio
async def test_long_press_cancelled_on_release() -> None:
    events: list[ButtonEvent] = []

    async def cb(e: ButtonEvent) -> None:
        events.append(e)

    transport = StubTransport(_status_response({"Bleep": False}))
    async with GoXLRClient(transport, on_button_event=cb, long_press_threshold=0.5) as client:
        await client.get_status()
        await transport.push_patch(_patch_ops("Bleep", True))
        await asyncio.sleep(0.01)  # short hold, well under threshold
        await transport.push_patch(_patch_ops("Bleep", False))
        await asyncio.sleep(0.6)  # wait past threshold — no long_press should fire

    types = [e.event_type for e in events]
    assert ButtonEventType.long_pressed not in types
    assert ButtonEventType.pressed in types
    assert ButtonEventType.released in types


@pytest.mark.asyncio
async def test_no_events_without_callback() -> None:
    """No button tracking overhead when no callback is registered."""
    transport = StubTransport(_status_response({"Bleep": False}))
    async with GoXLRClient(transport) as client:
        await client.get_status()
        await transport.push_patch(_patch_ops("Bleep", True))
    # Should not raise


@pytest.mark.asyncio
async def test_button_enum_resolved() -> None:
    events: list[ButtonEvent] = []

    async def cb(e: ButtonEvent) -> None:
        events.append(e)

    transport = StubTransport(_status_response({"EffectFx": False}))
    async with GoXLRClient(transport, on_button_event=cb) as client:
        await client.get_status()
        await transport.push_patch(_patch_ops("EffectFx", True))

    from goxlrutil_api.protocol.types import Button
    assert events[0].button_enum == Button.EffectFx


@pytest.mark.asyncio
async def test_unknown_button_does_not_crash() -> None:
    events: list[ButtonEvent] = []

    async def cb(e: ButtonEvent) -> None:
        events.append(e)

    transport = StubTransport(_status_response({"FutureButton": False}))
    async with GoXLRClient(transport, on_button_event=cb) as client:
        await client.get_status()
        await transport.push_patch(_patch_ops("FutureButton", True))

    assert events[0].button == "FutureButton"
    assert events[0].button_enum is None
