"""Protocol commands: DaemonRequest, DaemonCommand, GoXLRCommand."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from goxlrutil_api.protocol.types import (
    Button,
    ChannelName,
    EchoStyle,
    EffectBankPresets,
    FaderName,
    GenderStyle,
    InputDevice,
    MicrophoneType,
    MuteFunction,
    MuteState,
    OutputDevice,
    PitchStyle,
    ReverbStyle,
    SampleBank,
    SampleButtons,
    VodMode,
)


def _to_json(obj: Any) -> Any:  # noqa: ANN401
    """Recursively convert a command to a JSON-serialisable structure."""
    if isinstance(obj, str):
        return obj
    if isinstance(obj, bool):
        return obj
    if isinstance(obj, (int, float)):
        return obj
    if obj is None:
        return None
    if isinstance(obj, Path):
        return str(obj)
    if isinstance(obj, list):
        return [_to_json(v) for v in obj]
    if isinstance(obj, tuple):
        return [_to_json(v) for v in obj]
    if hasattr(obj, "value"):  # Enum
        return obj.value
    if hasattr(obj, "__dict__"):
        return {k: _to_json(v) for k, v in obj.__dict__.items() if not k.startswith("_")}
    return obj


# ---------------------------------------------------------------------------
# DaemonCommand
# ---------------------------------------------------------------------------

@dataclass
class DaemonCommand:
    """Commands targeting the daemon itself (not a specific mixer)."""

    _variant: str
    _args: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        if self._args:
            return {self._variant: _to_json(self._args)}
        return self._variant  # type: ignore[return-value]  # plain string variant

    # -- Factories -----------------------------------------------------------

    @staticmethod
    def open_ui() -> DaemonCommand:
        return DaemonCommand("OpenUi")

    @staticmethod
    def stop_daemon() -> DaemonCommand:
        return DaemonCommand("StopDaemon")

    @staticmethod
    def set_allow_network_access(allow: bool) -> DaemonCommand:
        return DaemonCommand("SetAllowNetworkAccess", {"SetAllowNetworkAccess": allow})


# ---------------------------------------------------------------------------
# GoXLRCommand
# ---------------------------------------------------------------------------

@dataclass
class GoXLRCommand:
    """A command targeting a specific GoXLR mixer."""

    _variant: str
    _payload: Any = None

    def to_dict(self) -> str | dict[str, object]:  # type: ignore[return]
        if self._payload is None:
            return self._variant
        return {self._variant: _to_json(self._payload)}

    @staticmethod
    def set_fader(fader: FaderName, channel: ChannelName) -> GoXLRCommand:
        return GoXLRCommand("SetFader", [fader, channel])

    @staticmethod
    def set_fader_mute_function(fader: FaderName, mute: MuteFunction) -> GoXLRCommand:
        return GoXLRCommand("SetFaderMuteFunction", [fader, mute])

    # -- Volumes -------------------------------------------------------------

    @staticmethod
    def set_volume(channel: ChannelName, volume: int) -> GoXLRCommand:
        """volume 0-255"""
        return GoXLRCommand("SetVolume", [channel, volume])

    # -- Mute states ---------------------------------------------------------

    @staticmethod
    def set_fader_mute_state(fader: FaderName, state: MuteState) -> GoXLRCommand:
        return GoXLRCommand("SetFaderMuteState", [fader, state])

    @staticmethod
    def set_cough_mute_state(state: MuteState) -> GoXLRCommand:
        return GoXLRCommand("SetCoughMuteState", state)

    # -- Routing -------------------------------------------------------------

    @staticmethod
    def set_router(inp: InputDevice, out: OutputDevice, enabled: bool) -> GoXLRCommand:
        return GoXLRCommand("SetRouter", [inp, out, enabled])

    # -- Effects -------------------------------------------------------------

    @staticmethod
    def set_fx_enabled(enabled: bool) -> GoXLRCommand:
        return GoXLRCommand("SetFXEnabled", enabled)

    @staticmethod
    def set_megaphone_enabled(enabled: bool) -> GoXLRCommand:
        return GoXLRCommand("SetMegaphoneEnabled", enabled)

    @staticmethod
    def set_robot_enabled(enabled: bool) -> GoXLRCommand:
        return GoXLRCommand("SetRobotEnabled", enabled)

    @staticmethod
    def set_hard_tune_enabled(enabled: bool) -> GoXLRCommand:
        return GoXLRCommand("SetHardTuneEnabled", enabled)

    @staticmethod
    def set_active_effect_preset(preset: EffectBankPresets) -> GoXLRCommand:
        return GoXLRCommand("SetActiveEffectPreset", preset)

    # -- Reverb --------------------------------------------------------------

    @staticmethod
    def set_reverb_style(style: ReverbStyle) -> GoXLRCommand:
        return GoXLRCommand("SetReverbStyle", style)

    @staticmethod
    def set_reverb_amount(amount: int) -> GoXLRCommand:
        return GoXLRCommand("SetReverbAmount", amount)

    # -- Echo ----------------------------------------------------------------

    @staticmethod
    def set_echo_style(style: EchoStyle) -> GoXLRCommand:
        return GoXLRCommand("SetEchoStyle", style)

    @staticmethod
    def set_echo_amount(amount: int) -> GoXLRCommand:
        return GoXLRCommand("SetEchoAmount", amount)

    # -- Pitch ---------------------------------------------------------------

    @staticmethod
    def set_pitch_style(style: PitchStyle) -> GoXLRCommand:
        return GoXLRCommand("SetPitchStyle", style)

    @staticmethod
    def set_pitch_amount(amount: int) -> GoXLRCommand:
        return GoXLRCommand("SetPitchAmount", amount)

    # -- Gender --------------------------------------------------------------

    @staticmethod
    def set_gender_style(style: GenderStyle) -> GoXLRCommand:
        return GoXLRCommand("SetGenderStyle", style)

    @staticmethod
    def set_gender_amount(amount: int) -> GoXLRCommand:
        return GoXLRCommand("SetGenderAmount", amount)

    # -- Sampler -------------------------------------------------------------

    @staticmethod
    def set_active_sampler_bank(bank: SampleBank) -> GoXLRCommand:
        return GoXLRCommand("SetActiveSamplerBank", bank)

    @staticmethod
    def play_next_sample(bank: SampleBank, button: SampleButtons) -> GoXLRCommand:
        return GoXLRCommand("PlayNextSample", [bank, button])

    @staticmethod
    def stop_sample_playback(bank: SampleBank, button: SampleButtons) -> GoXLRCommand:
        return GoXLRCommand("StopSamplePlayback", [bank, button])

    # -- Lighting ------------------------------------------------------------

    @staticmethod
    def set_button_colours(
        button: Button, colour_one: str, colour_two: str | None = None
    ) -> GoXLRCommand:
        return GoXLRCommand("SetButtonColours", [button, colour_one, colour_two])

    @staticmethod
    def set_fader_colours(
        fader: FaderName, colour_one: str, colour_two: str
    ) -> GoXLRCommand:
        return GoXLRCommand("SetFaderColours", [fader, colour_one, colour_two])

    @staticmethod
    def set_global_colour(colour: str) -> GoXLRCommand:
        return GoXLRCommand("SetGlobalColour", colour)

    # -- Mic / EQ ------------------------------------------------------------

    @staticmethod
    def set_microphone_type(mic_type: MicrophoneType) -> GoXLRCommand:
        return GoXLRCommand("SetMicrophoneType", mic_type)

    @staticmethod
    def set_gate_threshold(threshold: int) -> GoXLRCommand:
        return GoXLRCommand("SetGateThreshold", threshold)

    @staticmethod
    def set_gate_active(active: bool) -> GoXLRCommand:
        return GoXLRCommand("SetGateActive", active)

    # -- Profiles ------------------------------------------------------------

    @staticmethod
    def load_profile(name: str, persist: bool = True) -> GoXLRCommand:
        return GoXLRCommand("LoadProfile", [name, persist])

    @staticmethod
    def save_profile() -> GoXLRCommand:
        return GoXLRCommand("SaveProfile", None)

    @staticmethod
    def load_mic_profile(name: str, persist: bool = True) -> GoXLRCommand:
        return GoXLRCommand("LoadMicProfile", [name, persist])

    # -- General settings ----------------------------------------------------

    @staticmethod
    def set_vod_mode(mode: VodMode) -> GoXLRCommand:
        return GoXLRCommand("SetVodMode", mode)

    @staticmethod
    def set_monitor_with_fx(enabled: bool) -> GoXLRCommand:
        return GoXLRCommand("SetMonitorWithFx", enabled)

    @staticmethod
    def set_swear_button_volume(volume: int) -> GoXLRCommand:
        """volume -36..36"""
        return GoXLRCommand("SetSwearButtonVolume", volume)

    @staticmethod
    def set_submix_enabled(enabled: bool) -> GoXLRCommand:
        return GoXLRCommand("SetSubMixEnabled", enabled)

    @staticmethod
    def set_submix_volume(channel: ChannelName, volume: int) -> GoXLRCommand:
        return GoXLRCommand("SetSubMixVolume", [channel, volume])

    @staticmethod
    def set_monitor_mix(output: OutputDevice) -> GoXLRCommand:
        return GoXLRCommand("SetMonitorMix", output)


# ---------------------------------------------------------------------------
# DaemonRequest (top-level message sent to daemon)
# ---------------------------------------------------------------------------

@dataclass
class DaemonRequest:
    _variant: str
    _payload: Any = None

    def to_dict(self) -> str | dict[str, object]:  # type: ignore[return]
        if self._payload is None:
            return self._variant
        return {self._variant: _to_json(self._payload)}

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    # -- Factories -----------------------------------------------------------

    @staticmethod
    def ping() -> DaemonRequest:
        return DaemonRequest("Ping")

    @staticmethod
    def get_status() -> DaemonRequest:
        return DaemonRequest("GetStatus")

    @staticmethod
    def get_mic_level(serial: str) -> DaemonRequest:
        return DaemonRequest("GetMicLevel", serial)

    @staticmethod
    def command(serial: str, cmd: GoXLRCommand) -> DaemonRequest:
        return DaemonRequest("Command", [serial, cmd.to_dict()])

    @staticmethod
    def daemon(cmd: DaemonCommand) -> DaemonRequest:
        return DaemonRequest("Daemon", cmd.to_dict())
