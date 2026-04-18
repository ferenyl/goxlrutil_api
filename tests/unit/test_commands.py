"""Tests for command serialisation round-trips."""

from __future__ import annotations

import json

from goxlrutil_api.protocol.commands import DaemonRequest, GoXLRCommand
from goxlrutil_api.protocol.types import ChannelName, FaderName, MuteState


def test_ping_serialises_as_string() -> None:
    req = DaemonRequest.ping()
    assert req.to_dict() == "Ping"
    assert json.loads(req.to_json()) == "Ping"


def test_get_status_serialises_as_string() -> None:
    assert DaemonRequest.get_status().to_dict() == "GetStatus"


def test_command_serialises_with_serial_and_payload() -> None:
    cmd = GoXLRCommand.set_volume(ChannelName.Mic, 200)
    req = DaemonRequest.command("SERIAL_001", cmd)
    data = req.to_dict()
    assert data == {"Command": ["SERIAL_001", {"SetVolume": ["Mic", 200]}]}


def test_set_fader_mute_state_serialises() -> None:
    cmd = GoXLRCommand.set_fader_mute_state(FaderName.A, MuteState.MutedToAll)
    assert cmd.to_dict() == {"SetFaderMuteState": ["A", "MutedToAll"]}


def test_set_fx_enabled_true() -> None:
    cmd = GoXLRCommand.set_fx_enabled(True)
    assert cmd.to_dict() == {"SetFXEnabled": True}


def test_set_fx_enabled_false() -> None:
    cmd = GoXLRCommand.set_fx_enabled(False)
    assert cmd.to_dict() == {"SetFXEnabled": False}


def test_get_mic_level_contains_serial() -> None:
    req = DaemonRequest.get_mic_level("ABC123")
    data = req.to_dict()
    assert data == {"GetMicLevel": "ABC123"}


def test_json_roundtrip_is_valid_json() -> None:
    req = DaemonRequest.command("X", GoXLRCommand.set_volume(ChannelName.Game, 128))
    parsed = json.loads(req.to_json())
    assert parsed["Command"][1] == {"SetVolume": ["Game", 128]}
