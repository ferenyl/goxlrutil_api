"""Protocol commands: DaemonRequest, DaemonCommand, GoXLRCommand."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, cast

from goxlrutil_api.protocol.types import (
    AnimationMode,
    Button,
    ButtonColourGroups,
    ButtonColourOffStyle,
    ChannelName,
    CompressorAttackTime,
    CompressorRatio,
    CompressorReleaseTime,
    DisplayMode,
    DisplayModeComponents,
    EchoStyle,
    EffectBankPresets,
    EncoderColourTargets,
    EqFrequencies,
    FaderDisplayStyle,
    FaderName,
    GateTimes,
    GenderStyle,
    HardTuneSource,
    HardTuneStyle,
    InputDevice,
    MegaphoneStyle,
    MicrophoneType,
    MiniEqFrequencies,
    Mix,
    MuteFunction,
    MuteState,
    OutputDevice,
    PitchStyle,
    ReverbStyle,
    RobotRange,
    RobotStyle,
    SampleBank,
    SampleButtons,
    SamplePlaybackMode,
    SamplePlayOrder,
    SamplerColourTargets,
    SimpleColourTargets,
    VodMode,
    WaterfallDirection,
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
        return [_to_json(v) for v in cast(list[Any], obj)]
    if isinstance(obj, tuple):
        return [_to_json(v) for v in cast(tuple[Any, ...], obj)]
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
    _args: dict[str, Any] = field(default_factory=dict[str, Any])

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

    @staticmethod
    def set_cough_mute_function(mute: MuteFunction) -> GoXLRCommand:
        return GoXLRCommand("SetCoughMuteFunction", mute)

    @staticmethod
    def set_cough_is_hold(hold: bool) -> GoXLRCommand:
        return GoXLRCommand("SetCoughIsHold", hold)

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
    def set_megaphone_style(style: MegaphoneStyle) -> GoXLRCommand:
        return GoXLRCommand("SetMegaphoneStyle", style)

    @staticmethod
    def set_megaphone_amount(amount: int) -> GoXLRCommand:
        """amount 0–100"""
        return GoXLRCommand("SetMegaphoneAmount", amount)

    @staticmethod
    def set_megaphone_post_gain(gain: int) -> GoXLRCommand:
        """gain -20..20 dB"""
        return GoXLRCommand("SetMegaphonePostGain", gain)

    @staticmethod
    def set_robot_enabled(enabled: bool) -> GoXLRCommand:
        return GoXLRCommand("SetRobotEnabled", enabled)

    @staticmethod
    def set_robot_style(style: RobotStyle) -> GoXLRCommand:
        return GoXLRCommand("SetRobotStyle", style)

    @staticmethod
    def set_robot_gain(range_: RobotRange, gain: int) -> GoXLRCommand:
        return GoXLRCommand("SetRobotGain", [range_, gain])

    @staticmethod
    def set_robot_freq(range_: RobotRange, freq: int) -> GoXLRCommand:
        return GoXLRCommand("SetRobotFreq", [range_, freq])

    @staticmethod
    def set_robot_width(range_: RobotRange, width: int) -> GoXLRCommand:
        return GoXLRCommand("SetRobotWidth", [range_, width])

    @staticmethod
    def set_robot_waveform(waveform: int) -> GoXLRCommand:
        """waveform 0–5"""
        return GoXLRCommand("SetRobotWaveform", waveform)

    @staticmethod
    def set_robot_pulse_width(width: int) -> GoXLRCommand:
        """width 0–100"""
        return GoXLRCommand("SetRobotPulseWidth", width)

    @staticmethod
    def set_robot_threshold(threshold: int) -> GoXLRCommand:
        return GoXLRCommand("SetRobotThreshold", threshold)

    @staticmethod
    def set_robot_dry_mix(mix: int) -> GoXLRCommand:
        return GoXLRCommand("SetRobotDryMix", mix)

    @staticmethod
    def set_hard_tune_enabled(enabled: bool) -> GoXLRCommand:
        return GoXLRCommand("SetHardTuneEnabled", enabled)

    @staticmethod
    def set_hard_tune_style(style: HardTuneStyle) -> GoXLRCommand:
        return GoXLRCommand("SetHardTuneStyle", style)

    @staticmethod
    def set_hard_tune_amount(amount: int) -> GoXLRCommand:
        """amount 0–100"""
        return GoXLRCommand("SetHardTuneAmount", amount)

    @staticmethod
    def set_hard_tune_rate(rate: int) -> GoXLRCommand:
        """rate 0–100"""
        return GoXLRCommand("SetHardTuneRate", rate)

    @staticmethod
    def set_hard_tune_window(window: int) -> GoXLRCommand:
        """window ms"""
        return GoXLRCommand("SetHardTuneWindow", window)

    @staticmethod
    def set_hard_tune_source(source: HardTuneSource) -> GoXLRCommand:
        return GoXLRCommand("SetHardTuneSource", source)

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

    @staticmethod
    def set_reverb_decay(ms: int) -> GoXLRCommand:
        return GoXLRCommand("SetReverbDecay", ms)

    @staticmethod
    def set_reverb_early_level(level: int) -> GoXLRCommand:
        return GoXLRCommand("SetReverbEarlyLevel", level)

    @staticmethod
    def set_reverb_tail_level(level: int) -> GoXLRCommand:
        return GoXLRCommand("SetReverbTailLevel", level)

    @staticmethod
    def set_reverb_pre_delay(ms: int) -> GoXLRCommand:
        return GoXLRCommand("SetReverbPreDelay", ms)

    @staticmethod
    def set_reverb_low_colour(colour: int) -> GoXLRCommand:
        return GoXLRCommand("SetReverbLowColour", colour)

    @staticmethod
    def set_reverb_high_colour(colour: int) -> GoXLRCommand:
        return GoXLRCommand("SetReverbHighColour", colour)

    @staticmethod
    def set_reverb_high_factor(factor: int) -> GoXLRCommand:
        return GoXLRCommand("SetReverbHighFactor", factor)

    @staticmethod
    def set_reverb_diffuse(diffuse: int) -> GoXLRCommand:
        return GoXLRCommand("SetReverbDiffuse", diffuse)

    @staticmethod
    def set_reverb_mod_speed(speed: int) -> GoXLRCommand:
        return GoXLRCommand("SetReverbModSpeed", speed)

    @staticmethod
    def set_reverb_mod_depth(depth: int) -> GoXLRCommand:
        return GoXLRCommand("SetReverbModDepth", depth)

    # -- Echo ----------------------------------------------------------------

    @staticmethod
    def set_echo_style(style: EchoStyle) -> GoXLRCommand:
        return GoXLRCommand("SetEchoStyle", style)

    @staticmethod
    def set_echo_amount(amount: int) -> GoXLRCommand:
        return GoXLRCommand("SetEchoAmount", amount)

    @staticmethod
    def set_echo_feedback(feedback: int) -> GoXLRCommand:
        """feedback 0–100"""
        return GoXLRCommand("SetEchoFeedback", feedback)

    @staticmethod
    def set_echo_tempo(bpm: int) -> GoXLRCommand:
        return GoXLRCommand("SetEchoTempo", bpm)

    @staticmethod
    def set_echo_delay_left(ms: int) -> GoXLRCommand:
        return GoXLRCommand("SetEchoDelayLeft", ms)

    @staticmethod
    def set_echo_delay_right(ms: int) -> GoXLRCommand:
        return GoXLRCommand("SetEchoDelayRight", ms)

    @staticmethod
    def set_echo_feedback_left(feedback: int) -> GoXLRCommand:
        return GoXLRCommand("SetEchoFeedbackLeft", feedback)

    @staticmethod
    def set_echo_feedback_right(feedback: int) -> GoXLRCommand:
        return GoXLRCommand("SetEchoFeedbackRight", feedback)

    @staticmethod
    def set_echo_xfb_l_to_r(feedback: int) -> GoXLRCommand:
        return GoXLRCommand("SetEchoFeedbackXFBLtoR", feedback)

    @staticmethod
    def set_echo_xfb_r_to_l(feedback: int) -> GoXLRCommand:
        return GoXLRCommand("SetEchoFeedbackXFBRtoL", feedback)

    # -- Pitch ---------------------------------------------------------------

    @staticmethod
    def set_pitch_style(style: PitchStyle) -> GoXLRCommand:
        return GoXLRCommand("SetPitchStyle", style)

    @staticmethod
    def set_pitch_amount(amount: int) -> GoXLRCommand:
        return GoXLRCommand("SetPitchAmount", amount)

    @staticmethod
    def set_pitch_character(character: int) -> GoXLRCommand:
        """character 0–100"""
        return GoXLRCommand("SetPitchCharacter", character)

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

    # -- Sampler management --------------------------------------------------

    @staticmethod
    def set_sampler_function(
        bank: SampleBank, button: SampleButtons, mode: SamplePlaybackMode
    ) -> GoXLRCommand:
        return GoXLRCommand("SetSamplerFunction", [bank, button, mode])

    @staticmethod
    def set_sampler_order(
        bank: SampleBank, button: SampleButtons, order: SamplePlayOrder
    ) -> GoXLRCommand:
        return GoXLRCommand("SetSamplerOrder", [bank, button, order])

    @staticmethod
    def add_sample(bank: SampleBank, button: SampleButtons, path: str) -> GoXLRCommand:
        return GoXLRCommand("AddSample", [bank, button, path])

    @staticmethod
    def remove_sample_by_index(
        bank: SampleBank, button: SampleButtons, index: int
    ) -> GoXLRCommand:
        return GoXLRCommand("RemoveSampleByIndex", [bank, button, index])

    @staticmethod
    def set_sample_start_percent(
        bank: SampleBank, button: SampleButtons, index: int, percent: float
    ) -> GoXLRCommand:
        return GoXLRCommand("SetSampleStartPercent", [bank, button, index, percent])

    @staticmethod
    def set_sample_stop_percent(
        bank: SampleBank, button: SampleButtons, index: int, percent: float
    ) -> GoXLRCommand:
        return GoXLRCommand("SetSampleStopPercent", [bank, button, index, percent])

    @staticmethod
    def set_sampler_fade_duration(ms: int) -> GoXLRCommand:
        return GoXLRCommand("SetSamplerFadeDuration", ms)

    @staticmethod
    def set_sampler_reset_on_clear(reset: bool) -> GoXLRCommand:
        return GoXLRCommand("SetSamplerResetOnClear", reset)

    # -- Lighting ------------------------------------------------------------

    @staticmethod
    def set_button_colours(
        button: Button, colour_one: str, colour_two: str | None = None
    ) -> GoXLRCommand:
        """Set the active/inactive LED colours for a single button."""
        return GoXLRCommand("SetButtonColours", [button, colour_one, colour_two])

    @staticmethod
    def set_button_off_style(
        button: Button, off_style: ButtonColourOffStyle, colour_two: str
    ) -> GoXLRCommand:
        """Set how a button appears when it is in the 'off' state."""
        return GoXLRCommand("SetButtonOffStyle", [button, off_style, colour_two])

    @staticmethod
    def set_button_group_colours(
        group: ButtonColourGroups, colour_one: str, colour_two: str
    ) -> GoXLRCommand:
        """Set LED colours for all buttons in a named group simultaneously."""
        return GoXLRCommand("SetButtonGroupColours", [group, colour_one, colour_two])

    @staticmethod
    def set_button_group_off_style(
        group: ButtonColourGroups, off_style: ButtonColourOffStyle, colour_two: str
    ) -> GoXLRCommand:
        """Set the off-state style for all buttons in a named group."""
        return GoXLRCommand("SetButtonGroupOffStyle", [group, off_style, colour_two])

    @staticmethod
    def set_fader_colours(
        fader: FaderName, colour_one: str, colour_two: str
    ) -> GoXLRCommand:
        """Set the two LED colours for a fader channel strip."""
        return GoXLRCommand("SetFaderColours", [fader, colour_one, colour_two])

    @staticmethod
    def set_fader_display_style(
        fader: FaderName, style: FaderDisplayStyle
    ) -> GoXLRCommand:
        """Set the display style (gradient, meter, etc.) for a single fader."""
        return GoXLRCommand("SetFaderDisplayStyle", [fader, style])

    @staticmethod
    def set_all_fader_display_style(style: FaderDisplayStyle) -> GoXLRCommand:
        """Apply the same display style to all four faders at once."""
        return GoXLRCommand("SetAllFaderDisplayStyle", style)

    @staticmethod
    def set_global_colour(colour: str) -> GoXLRCommand:
        """Set the global accent colour used by animations and unassigned LEDs."""
        return GoXLRCommand("SetGlobalColour", colour)

    @staticmethod
    def set_simple_colour(
        target: SimpleColourTargets, colour: str
    ) -> GoXLRCommand:
        """Set the colour for a simple single-colour target (Global, Accent, ScribbleBack)."""
        return GoXLRCommand("SetSimpleColour", [target, colour])

    @staticmethod
    def set_encoder_colour(
        target: EncoderColourTargets,
        colour_left: str,
        colour_right: str,
        colour_knob: str,
    ) -> GoXLRCommand:
        """Set the three LED zones of an encoder (left arc, right arc, knob)."""
        return GoXLRCommand("SetEncoderColour", [target, colour_left, colour_right, colour_knob])

    @staticmethod
    def set_sampler_colour(
        target: SamplerColourTargets,
        colour_one: str,
        colour_two: str,
        colour_three: str,
    ) -> GoXLRCommand:
        """Set the three LED states for a sampler bank selector button."""
        return GoXLRCommand("SetSamplerColour", [target, colour_one, colour_two, colour_three])

    @staticmethod
    def set_sampler_off_style(
        target: SamplerColourTargets, off_style: ButtonColourOffStyle, colour_two: str
    ) -> GoXLRCommand:
        """Set the off-state style for a sampler bank selector button."""
        return GoXLRCommand("SetSamplerOffStyle", [target, off_style, colour_two])

    @staticmethod
    def set_animation_mode(
        mode: AnimationMode,
        colour_one: str,
        colour_two: str,
        waterfall: WaterfallDirection,
    ) -> GoXLRCommand:
        """Set the global LED animation mode and parameters."""
        return GoXLRCommand("SetAnimationMode", [mode, colour_one, colour_two, waterfall])

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

    @staticmethod
    def set_gate_attenuation(attenuation: int) -> GoXLRCommand:
        """attenuation 0–100 %"""
        return GoXLRCommand("SetGateAttenuation", attenuation)

    @staticmethod
    def set_gate_attack(attack: GateTimes) -> GoXLRCommand:
        return GoXLRCommand("SetGateAttack", attack)

    @staticmethod
    def set_gate_release(release: GateTimes) -> GoXLRCommand:
        return GoXLRCommand("SetGateRelease", release)

    # -- EQ ------------------------------------------------------------------

    @staticmethod
    def set_eq_gain(freq: EqFrequencies, gain: int) -> GoXLRCommand:
        """gain -9..9 dB"""
        return GoXLRCommand("SetEqGain", [freq, gain])

    @staticmethod
    def set_eq_freq(freq: EqFrequencies, value: float) -> GoXLRCommand:
        return GoXLRCommand("SetEqFreq", [freq, value])

    @staticmethod
    def set_eq_mini_gain(freq: MiniEqFrequencies, gain: int) -> GoXLRCommand:
        """gain -9..9 dB"""
        return GoXLRCommand("SetEqMiniGain", [freq, gain])

    @staticmethod
    def set_eq_mini_freq(freq: MiniEqFrequencies, value: float) -> GoXLRCommand:
        return GoXLRCommand("SetEqMiniFreq", [freq, value])

    # -- Compressor ----------------------------------------------------------

    @staticmethod
    def set_compressor_threshold(threshold: int) -> GoXLRCommand:
        """threshold -40..0 dB"""
        return GoXLRCommand("SetCompressorThreshold", threshold)

    @staticmethod
    def set_compressor_ratio(ratio: CompressorRatio) -> GoXLRCommand:
        return GoXLRCommand("SetCompressorRatio", ratio)

    @staticmethod
    def set_compressor_attack(attack: CompressorAttackTime) -> GoXLRCommand:
        return GoXLRCommand("SetCompressorAttack", attack)

    @staticmethod
    def set_compressor_release(release: CompressorReleaseTime) -> GoXLRCommand:
        return GoXLRCommand("SetCompressorReleaseTime", release)

    @staticmethod
    def set_compressor_makeup_gain(gain: int) -> GoXLRCommand:
        """gain 0..24 dB"""
        return GoXLRCommand("SetCompressorMakeupGain", gain)

    # -- De-esser ------------------------------------------------------------

    @staticmethod
    def set_deeser(amount: int) -> GoXLRCommand:
        """amount 0..100"""
        return GoXLRCommand("SetDeeser", amount)

    # -- Mic gain ------------------------------------------------------------

    @staticmethod
    def set_microphone_gain(mic_type: MicrophoneType, gain: int) -> GoXLRCommand:
        """gain 0..72 dB"""
        return GoXLRCommand("SetMicrophoneGain", [mic_type, gain])

    # -- Scribble strips -----------------------------------------------------

    @staticmethod
    def set_scribble_text(fader: FaderName, text: str) -> GoXLRCommand:
        return GoXLRCommand("SetScribbleText", [fader, text])

    @staticmethod
    def set_scribble_icon(fader: FaderName, icon: str | None) -> GoXLRCommand:
        return GoXLRCommand("SetScribbleIcon", [fader, icon])

    @staticmethod
    def set_scribble_number(fader: FaderName, number: str) -> GoXLRCommand:
        return GoXLRCommand("SetScribbleNumber", [fader, number])

    @staticmethod
    def set_scribble_invert(fader: FaderName, invert: bool) -> GoXLRCommand:
        return GoXLRCommand("SetScribbleInvert", [fader, invert])

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
        """volume -34..0"""
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

    # -- Submix extras -------------------------------------------------------

    @staticmethod
    def set_submix_linked(channel: ChannelName, linked: bool) -> GoXLRCommand:
        return GoXLRCommand("SetSubMixLinked", [channel, linked])

    @staticmethod
    def set_submix_output_mix(output: OutputDevice, mix: Mix) -> GoXLRCommand:
        return GoXLRCommand("SetSubMixOutputMix", [output, mix])

    # -- Misc ----------------------------------------------------------------

    @staticmethod
    def set_lock_faders(locked: bool) -> GoXLRCommand:
        return GoXLRCommand("SetLockFaders", locked)

    @staticmethod
    def set_vc_mute_also_mute_cm(enabled: bool) -> GoXLRCommand:
        return GoXLRCommand("SetVCMuteAlsoMuteCM", enabled)

    @staticmethod
    def set_mute_hold_duration(ms: int) -> GoXLRCommand:
        return GoXLRCommand("SetMuteHoldDuration", ms)

    @staticmethod
    def set_element_display_mode(
        component: DisplayModeComponents, mode: DisplayMode
    ) -> GoXLRCommand:
        return GoXLRCommand("SetElementDisplayMode", [component, mode])

    # -- Profile extras ------------------------------------------------------

    @staticmethod
    def save_profile_as(name: str) -> GoXLRCommand:
        return GoXLRCommand("SaveProfileAs", name)

    @staticmethod
    def save_mic_profile() -> GoXLRCommand:
        return GoXLRCommand("SaveMicProfile", None)

    @staticmethod
    def save_mic_profile_as(name: str) -> GoXLRCommand:
        return GoXLRCommand("SaveMicProfileAs", name)

    @staticmethod
    def load_profile_colours(name: str) -> GoXLRCommand:
        return GoXLRCommand("LoadProfileColours", name)

    @staticmethod
    def rename_active_preset(name: str) -> GoXLRCommand:
        return GoXLRCommand("RenameActivePreset", name)

    # -- All fader colours ---------------------------------------------------

    @staticmethod
    def set_all_fader_colours(colour_one: str, colour_two: str) -> GoXLRCommand:
        return GoXLRCommand("SetAllFaderColours", [colour_one, colour_two])


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
