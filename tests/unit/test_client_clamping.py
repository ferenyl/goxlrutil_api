"""Tests for GoXLRClient value-clamping and convenience methods."""

from __future__ import annotations

from typing import Any

import pytest

from goxlrutil_api.client import GoXLRClient
from goxlrutil_api.protocol.commands import DaemonRequest
from goxlrutil_api.protocol.responses import DaemonResponse
from goxlrutil_api.protocol.types import ChannelName
from goxlrutil_api.transport.base import PatchCallback, Transport

# ---------------------------------------------------------------------------
# Minimal stub transport
# ---------------------------------------------------------------------------

class RecordingTransport(Transport):
    """Transport that records every command sent and returns a canned status."""

    def __init__(self, status_raw: dict[str, Any]) -> None:
        self._status_raw = status_raw
        self.sent: list[DaemonRequest] = []

    async def connect(self) -> None:
        pass

    async def disconnect(self) -> None:
        pass

    async def send(self, request: DaemonRequest) -> DaemonResponse:
        self.sent.append(request)
        return DaemonResponse(raw_status=self._status_raw)

    async def subscribe(self, callback: PatchCallback) -> None:
        pass


def _minimal_status() -> dict[str, Any]:
    return {
        "config": {"daemon_version": "1.0.0", "http_settings": {}},
        "mixers": {
            "SER001": {
                "hardware": {"device_type": "Full", "colour_way": "Black"},
                "fader_status": {
                    "A": {"channel": "Mic", "mute_state": "Unmuted"},
                },
                "levels": {"volumes": {"Mic": 128}, "output_monitor": "Headphones"},
                "cough_button": {},
                "button_down": {},
                "router": {},
                "profile_name": "Default",
                "mic_profile_name": "MicDefault",
            }
        },
        "paths": {},
        "files": {"profiles": ["Default"], "mic_profiles": ["MicDefault"]},
    }


# ---------------------------------------------------------------------------
# Helper to extract the GoXLRCommand sent for a given command serial
# ---------------------------------------------------------------------------

def _last_goxlr_cmd(transport: RecordingTransport) -> dict[str, Any]:
    """Return the inner GoXLR command payload from the most recent send."""
    req = transport.sent[-1]
    raw = req.to_dict()
    assert isinstance(raw, dict), f"Expected dict payload, got: {raw}"
    assert "Command" in raw, f"Expected Command key, got: {raw}"
    args = raw["Command"]
    assert isinstance(args, list) and len(args) >= 2, f"Unexpected Command value: {args}"
    result = args[1]
    assert isinstance(result, dict), f"Expected dict command, got: {result}"
    return result  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# set_swear_button_volume clamping
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_swear_volume_at_zero() -> None:
    t = RecordingTransport(_minimal_status())
    async with GoXLRClient(t) as client:
        await client.get_status()
        await client.set_swear_button_volume("SER001", 0)
    assert _last_goxlr_cmd(t) == {"SetSwearButtonVolume": 0}


@pytest.mark.asyncio
async def test_swear_volume_at_min() -> None:
    t = RecordingTransport(_minimal_status())
    async with GoXLRClient(t) as client:
        await client.get_status()
        await client.set_swear_button_volume("SER001", -34)
    assert _last_goxlr_cmd(t) == {"SetSwearButtonVolume": -34}


@pytest.mark.asyncio
async def test_swear_volume_clamped_above_max() -> None:
    """Values above 0 are clamped to 0."""
    t = RecordingTransport(_minimal_status())
    async with GoXLRClient(t) as client:
        await client.get_status()
        await client.set_swear_button_volume("SER001", 10)
    assert _last_goxlr_cmd(t) == {"SetSwearButtonVolume": 0}


@pytest.mark.asyncio
async def test_swear_volume_clamped_below_min() -> None:
    """Values below -34 are clamped to -34."""
    t = RecordingTransport(_minimal_status())
    async with GoXLRClient(t) as client:
        await client.get_status()
        await client.set_swear_button_volume("SER001", -100)
    assert _last_goxlr_cmd(t) == {"SetSwearButtonVolume": -34}


@pytest.mark.asyncio
async def test_swear_volume_rounds_float() -> None:
    """Fractional dB is rounded to nearest integer."""
    t = RecordingTransport(_minimal_status())
    async with GoXLRClient(t) as client:
        await client.get_status()
        await client.set_swear_button_volume("SER001", -5.6)
    assert _last_goxlr_cmd(t) == {"SetSwearButtonVolume": -6}


@pytest.mark.asyncio
async def test_swear_volume_rounds_up() -> None:
    t = RecordingTransport(_minimal_status())
    async with GoXLRClient(t) as client:
        await client.get_status()
        await client.set_swear_button_volume("SER001", -5.4)
    assert _last_goxlr_cmd(t) == {"SetSwearButtonVolume": -5}


# ---------------------------------------------------------------------------
# set_swear_button_volume_pct
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_swear_volume_pct_zero_gives_min() -> None:
    """0% → -34 dB (full duck)."""
    t = RecordingTransport(_minimal_status())
    async with GoXLRClient(t) as client:
        await client.get_status()
        await client.set_swear_button_volume_pct("SER001", 0.0)
    assert _last_goxlr_cmd(t) == {"SetSwearButtonVolume": -34}


@pytest.mark.asyncio
async def test_swear_volume_pct_hundred_gives_zero() -> None:
    """100% → 0 dB (no duck)."""
    t = RecordingTransport(_minimal_status())
    async with GoXLRClient(t) as client:
        await client.get_status()
        await client.set_swear_button_volume_pct("SER001", 100.0)
    assert _last_goxlr_cmd(t) == {"SetSwearButtonVolume": 0}


@pytest.mark.asyncio
async def test_swear_volume_pct_fifty() -> None:
    """50% → -17 dB."""
    t = RecordingTransport(_minimal_status())
    async with GoXLRClient(t) as client:
        await client.get_status()
        await client.set_swear_button_volume_pct("SER001", 50.0)
    assert _last_goxlr_cmd(t) == {"SetSwearButtonVolume": -17}


@pytest.mark.asyncio
async def test_swear_volume_pct_clamped_above_100() -> None:
    t = RecordingTransport(_minimal_status())
    async with GoXLRClient(t) as client:
        await client.get_status()
        await client.set_swear_button_volume_pct("SER001", 150.0)
    assert _last_goxlr_cmd(t) == {"SetSwearButtonVolume": 0}


@pytest.mark.asyncio
async def test_swear_volume_pct_clamped_below_zero() -> None:
    t = RecordingTransport(_minimal_status())
    async with GoXLRClient(t) as client:
        await client.get_status()
        await client.set_swear_button_volume_pct("SER001", -10.0)
    assert _last_goxlr_cmd(t) == {"SetSwearButtonVolume": -34}


# ---------------------------------------------------------------------------
# set_volume_pct
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_volume_pct_zero() -> None:
    """0% → volume 0."""
    t = RecordingTransport(_minimal_status())
    async with GoXLRClient(t) as client:
        await client.get_status()
        await client.set_volume_pct("SER001", ChannelName.Mic, 0.0)
    assert _last_goxlr_cmd(t) == {"SetVolume": ["Mic", 0]}


@pytest.mark.asyncio
async def test_volume_pct_hundred() -> None:
    """100% → volume 255."""
    t = RecordingTransport(_minimal_status())
    async with GoXLRClient(t) as client:
        await client.get_status()
        await client.set_volume_pct("SER001", ChannelName.Mic, 100.0)
    assert _last_goxlr_cmd(t) == {"SetVolume": ["Mic", 255]}


@pytest.mark.asyncio
async def test_volume_pct_fifty() -> None:
    """50% → volume 128 (rounded)."""
    t = RecordingTransport(_minimal_status())
    async with GoXLRClient(t) as client:
        await client.get_status()
        await client.set_volume_pct("SER001", ChannelName.Mic, 50.0)
    assert _last_goxlr_cmd(t) == {"SetVolume": ["Mic", 128]}


@pytest.mark.asyncio
async def test_volume_pct_clamped_above_100() -> None:
    t = RecordingTransport(_minimal_status())
    async with GoXLRClient(t) as client:
        await client.get_status()
        await client.set_volume_pct("SER001", ChannelName.Mic, 200.0)
    assert _last_goxlr_cmd(t) == {"SetVolume": ["Mic", 255]}


@pytest.mark.asyncio
async def test_volume_pct_clamped_below_0() -> None:
    t = RecordingTransport(_minimal_status())
    async with GoXLRClient(t) as client:
        await client.get_status()
        await client.set_volume_pct("SER001", ChannelName.Mic, -50.0)
    assert _last_goxlr_cmd(t) == {"SetVolume": ["Mic", 0]}


# ---------------------------------------------------------------------------
# get_mixer convenience
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_mixer_returns_none_before_status() -> None:
    t = RecordingTransport(_minimal_status())
    async with GoXLRClient(t) as client:
        assert client.get_mixer("SER001") is None


@pytest.mark.asyncio
async def test_get_mixer_returns_mixer_after_status() -> None:
    t = RecordingTransport(_minimal_status())
    async with GoXLRClient(t) as client:
        await client.get_status()
        mixer = client.get_mixer("SER001")
        assert mixer is not None
        assert mixer.profile_name == "Default"


@pytest.mark.asyncio
async def test_get_mixer_unknown_serial_returns_none() -> None:
    t = RecordingTransport(_minimal_status())
    async with GoXLRClient(t) as client:
        await client.get_status()
        assert client.get_mixer("UNKNOWN") is None


# ---------------------------------------------------------------------------
# serials property
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_serials_empty_before_status() -> None:
    t = RecordingTransport(_minimal_status())
    async with GoXLRClient(t) as client:
        assert client.serials == []


@pytest.mark.asyncio
async def test_serials_populated_after_status() -> None:
    t = RecordingTransport(_minimal_status())
    async with GoXLRClient(t) as client:
        await client.get_status()
        assert client.serials == ["SER001"]
