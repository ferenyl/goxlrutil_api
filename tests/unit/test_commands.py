"""Tests for command serialisation round-trips."""

from __future__ import annotations

import json

import pytest

from goxlrutil_api.protocol.commands import DaemonCommand, DaemonRequest, GoXLRCommand
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

# ---------------------------------------------------------------------------
# DaemonRequest helpers
# ---------------------------------------------------------------------------

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


def test_get_mic_level_contains_serial() -> None:
    req = DaemonRequest.get_mic_level("ABC123")
    assert req.to_dict() == {"GetMicLevel": "ABC123"}


def test_json_roundtrip_is_valid_json() -> None:
    req = DaemonRequest.command("X", GoXLRCommand.set_volume(ChannelName.Game, 128))
    parsed = json.loads(req.to_json())
    assert parsed["Command"][1] == {"SetVolume": ["Game", 128]}


def test_daemon_command_open_ui() -> None:
    assert DaemonRequest.daemon(DaemonCommand.open_ui()).to_dict() == {"Daemon": "OpenUi"}


def test_daemon_command_stop_daemon() -> None:
    assert DaemonRequest.daemon(DaemonCommand.stop_daemon()).to_dict() == {"Daemon": "StopDaemon"}


# ---------------------------------------------------------------------------
# Fader / mute
# ---------------------------------------------------------------------------

def test_set_fader_mute_state_serialises() -> None:
    cmd = GoXLRCommand.set_fader_mute_state(FaderName.A, MuteState.MutedToAll)
    assert cmd.to_dict() == {"SetFaderMuteState": ["A", "MutedToAll"]}


def test_set_fader_assigns_channel() -> None:
    cmd = GoXLRCommand.set_fader(FaderName.B, ChannelName.Game)
    assert cmd.to_dict() == {"SetFader": ["B", "Game"]}


def test_set_fader_mute_function() -> None:
    cmd = GoXLRCommand.set_fader_mute_function(FaderName.C, MuteFunction.All)
    assert cmd.to_dict() == {"SetFaderMuteFunction": ["C", "All"]}


def test_set_cough_mute_state() -> None:
    cmd = GoXLRCommand.set_cough_mute_state(MuteState.MutedToAll)
    assert cmd.to_dict() == {"SetCoughMuteState": "MutedToAll"}


def test_set_cough_is_hold_true() -> None:
    assert GoXLRCommand.set_cough_is_hold(True).to_dict() == {"SetCoughIsHold": True}


# ---------------------------------------------------------------------------
# FX toggles
# ---------------------------------------------------------------------------

def test_set_fx_enabled_true() -> None:
    assert GoXLRCommand.set_fx_enabled(True).to_dict() == {"SetFXEnabled": True}


def test_set_fx_enabled_false() -> None:
    assert GoXLRCommand.set_fx_enabled(False).to_dict() == {"SetFXEnabled": False}


def test_set_megaphone_enabled() -> None:
    assert GoXLRCommand.set_megaphone_enabled(True).to_dict() == {"SetMegaphoneEnabled": True}


def test_set_robot_enabled() -> None:
    assert GoXLRCommand.set_robot_enabled(False).to_dict() == {"SetRobotEnabled": False}


def test_set_hard_tune_enabled() -> None:
    assert GoXLRCommand.set_hard_tune_enabled(True).to_dict() == {"SetHardTuneEnabled": True}


def test_set_active_effect_preset() -> None:
    cmd = GoXLRCommand.set_active_effect_preset(EffectBankPresets.Preset1)
    assert cmd.to_dict() == {"SetActiveEffectPreset": "Preset1"}


# ---------------------------------------------------------------------------
# Megaphone details
# ---------------------------------------------------------------------------

def test_set_megaphone_style() -> None:
    cmd = GoXLRCommand.set_megaphone_style(MegaphoneStyle.Megaphone)
    assert cmd.to_dict() == {"SetMegaphoneStyle": "Megaphone"}


def test_set_megaphone_amount() -> None:
    assert GoXLRCommand.set_megaphone_amount(75).to_dict() == {"SetMegaphoneAmount": 75}


def test_set_megaphone_post_gain() -> None:
    assert GoXLRCommand.set_megaphone_post_gain(-5).to_dict() == {"SetMegaphonePostGain": -5}


# ---------------------------------------------------------------------------
# Robot details
# ---------------------------------------------------------------------------

def test_set_robot_style() -> None:
    cmd = GoXLRCommand.set_robot_style(RobotStyle.Robot1)
    assert cmd.to_dict() == {"SetRobotStyle": "Robot1"}


def test_set_robot_gain() -> None:
    cmd = GoXLRCommand.set_robot_gain(RobotRange.Low, 10)
    assert cmd.to_dict() == {"SetRobotGain": ["Low", 10]}


def test_set_robot_freq() -> None:
    cmd = GoXLRCommand.set_robot_freq(RobotRange.Medium, 500)
    assert cmd.to_dict() == {"SetRobotFreq": ["Medium", 500]}


def test_set_robot_width() -> None:
    cmd = GoXLRCommand.set_robot_width(RobotRange.High, 200)
    assert cmd.to_dict() == {"SetRobotWidth": ["High", 200]}


def test_set_robot_waveform() -> None:
    assert GoXLRCommand.set_robot_waveform(3).to_dict() == {"SetRobotWaveform": 3}


def test_set_robot_threshold() -> None:
    assert GoXLRCommand.set_robot_threshold(-10).to_dict() == {"SetRobotThreshold": -10}


# ---------------------------------------------------------------------------
# HardTune details
# ---------------------------------------------------------------------------

def test_set_hard_tune_style() -> None:
    cmd = GoXLRCommand.set_hard_tune_style(HardTuneStyle.Natural)
    assert cmd.to_dict() == {"SetHardTuneStyle": "Natural"}


def test_set_hard_tune_amount() -> None:
    assert GoXLRCommand.set_hard_tune_amount(50).to_dict() == {"SetHardTuneAmount": 50}


def test_set_hard_tune_source() -> None:
    cmd = GoXLRCommand.set_hard_tune_source(HardTuneSource.All)
    assert cmd.to_dict() == {"SetHardTuneSource": "All"}


# ---------------------------------------------------------------------------
# Reverb
# ---------------------------------------------------------------------------

def test_set_reverb_style() -> None:
    cmd = GoXLRCommand.set_reverb_style(ReverbStyle.Library)
    assert cmd.to_dict() == {"SetReverbStyle": "Library"}


def test_set_reverb_amount() -> None:
    assert GoXLRCommand.set_reverb_amount(80).to_dict() == {"SetReverbAmount": 80}


def test_set_reverb_decay() -> None:
    assert GoXLRCommand.set_reverb_decay(2000).to_dict() == {"SetReverbDecay": 2000}


def test_set_reverb_pre_delay() -> None:
    assert GoXLRCommand.set_reverb_pre_delay(20).to_dict() == {"SetReverbPreDelay": 20}


# ---------------------------------------------------------------------------
# Echo
# ---------------------------------------------------------------------------

def test_set_echo_style() -> None:
    cmd = GoXLRCommand.set_echo_style(EchoStyle.ClassicSlap)
    assert cmd.to_dict() == {"SetEchoStyle": "ClassicSlap"}


def test_set_echo_amount() -> None:
    assert GoXLRCommand.set_echo_amount(60).to_dict() == {"SetEchoAmount": 60}


def test_set_echo_feedback() -> None:
    assert GoXLRCommand.set_echo_feedback(40).to_dict() == {"SetEchoFeedback": 40}


def test_set_echo_delay_left() -> None:
    assert GoXLRCommand.set_echo_delay_left(250).to_dict() == {"SetEchoDelayLeft": 250}


def test_set_echo_xfb_l_to_r() -> None:
    assert GoXLRCommand.set_echo_xfb_l_to_r(20).to_dict() == {"SetEchoFeedbackXFBLtoR": 20}


# ---------------------------------------------------------------------------
# Pitch / Gender
# ---------------------------------------------------------------------------

def test_set_pitch_style() -> None:
    cmd = GoXLRCommand.set_pitch_style(PitchStyle.Narrow)
    assert cmd.to_dict() == {"SetPitchStyle": "Narrow"}


def test_set_pitch_amount() -> None:
    assert GoXLRCommand.set_pitch_amount(-12).to_dict() == {"SetPitchAmount": -12}


def test_set_pitch_character() -> None:
    assert GoXLRCommand.set_pitch_character(50).to_dict() == {"SetPitchCharacter": 50}


def test_set_gender_style() -> None:
    cmd = GoXLRCommand.set_gender_style(GenderStyle.Narrow)
    assert cmd.to_dict() == {"SetGenderStyle": "Narrow"}


def test_set_gender_amount() -> None:
    assert GoXLRCommand.set_gender_amount(-8).to_dict() == {"SetGenderAmount": -8}


# ---------------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------------

def test_set_router_enabled() -> None:
    cmd = GoXLRCommand.set_router(InputDevice.Microphone, OutputDevice.Headphones, True)
    assert cmd.to_dict() == {"SetRouter": ["Microphone", "Headphones", True]}


def test_set_router_disabled() -> None:
    cmd = GoXLRCommand.set_router(InputDevice.Chat, OutputDevice.BroadcastMix, False)
    assert cmd.to_dict() == {"SetRouter": ["Chat", "BroadcastMix", False]}


# ---------------------------------------------------------------------------
# Sampler
# ---------------------------------------------------------------------------

def test_play_next_sample() -> None:
    cmd = GoXLRCommand.play_next_sample(SampleBank.A, SampleButtons.TopLeft)
    assert cmd.to_dict() == {"PlayNextSample": ["A", "TopLeft"]}


def test_stop_sample_playback() -> None:
    cmd = GoXLRCommand.stop_sample_playback(SampleBank.B, SampleButtons.TopRight)
    assert cmd.to_dict() == {"StopSamplePlayback": ["B", "TopRight"]}


def test_set_sampler_function() -> None:
    cmd = GoXLRCommand.set_sampler_function(
        SampleBank.A, SampleButtons.TopLeft, SamplePlaybackMode.PlayNext
    )
    assert cmd.to_dict() == {"SetSamplerFunction": ["A", "TopLeft", "PlayNext"]}


def test_set_sampler_order() -> None:
    cmd = GoXLRCommand.set_sampler_order(
        SampleBank.B, SampleButtons.BottomLeft, SamplePlayOrder.Sequential
    )
    assert cmd.to_dict() == {"SetSamplerOrder": ["B", "BottomLeft", "Sequential"]}


def test_add_sample() -> None:
    cmd = GoXLRCommand.add_sample(SampleBank.C, SampleButtons.TopLeft, "/path/to/file.wav")
    assert cmd.to_dict() == {"AddSample": ["C", "TopLeft", "/path/to/file.wav"]}


def test_remove_sample_by_index() -> None:
    cmd = GoXLRCommand.remove_sample_by_index(SampleBank.A, SampleButtons.TopLeft, 0)
    assert cmd.to_dict() == {"RemoveSampleByIndex": ["A", "TopLeft", 0]}


# ---------------------------------------------------------------------------
# Mic / EQ
# ---------------------------------------------------------------------------

def test_set_microphone_type() -> None:
    cmd = GoXLRCommand.set_microphone_type(MicrophoneType.Condenser)
    assert cmd.to_dict() == {"SetMicrophoneType": "Condenser"}


def test_set_gate_threshold() -> None:
    assert GoXLRCommand.set_gate_threshold(-30).to_dict() == {"SetGateThreshold": -30}


def test_set_gate_active() -> None:
    assert GoXLRCommand.set_gate_active(True).to_dict() == {"SetGateActive": True}


def test_set_gate_attack() -> None:
    cmd = GoXLRCommand.set_gate_attack(GateTimes.Attack10ms)
    assert cmd.to_dict() == {"SetGateAttack": "Attack10ms"}


def test_set_gate_release() -> None:
    cmd = GoXLRCommand.set_gate_release(GateTimes.Attack100ms)
    assert cmd.to_dict() == {"SetGateRelease": "Attack100ms"}


def test_set_eq_gain() -> None:
    cmd = GoXLRCommand.set_eq_gain(EqFrequencies.Equalizer63Hz, 5)
    assert cmd.to_dict() == {"SetEqGain": ["Equalizer63Hz", 5]}


def test_set_eq_mini_gain() -> None:
    cmd = GoXLRCommand.set_eq_mini_gain(MiniEqFrequencies.Equalizer90Hz, -3)
    assert cmd.to_dict() == {"SetEqMiniGain": ["Equalizer90Hz", -3]}


def test_set_compressor_threshold() -> None:
    assert GoXLRCommand.set_compressor_threshold(-20).to_dict() == {"SetCompressorThreshold": -20}


def test_set_compressor_ratio() -> None:
    cmd = GoXLRCommand.set_compressor_ratio(CompressorRatio.Ratio2to1)
    assert cmd.to_dict() == {"SetCompressorRatio": "Ratio2to1"}


def test_set_compressor_attack() -> None:
    cmd = GoXLRCommand.set_compressor_attack(CompressorAttackTime.Attack2ms)
    assert cmd.to_dict() == {"SetCompressorAttack": "Attack2ms"}


def test_set_compressor_release() -> None:
    cmd = GoXLRCommand.set_compressor_release(CompressorReleaseTime.Release15ms)
    assert cmd.to_dict() == {"SetCompressorReleaseTime": "Release15ms"}


def test_set_compressor_makeup_gain() -> None:
    assert GoXLRCommand.set_compressor_makeup_gain(6).to_dict() == {"SetCompressorMakeupGain": 6}


def test_set_deeser() -> None:
    assert GoXLRCommand.set_deeser(30).to_dict() == {"SetDeeser": 30}


def test_set_microphone_gain() -> None:
    cmd = GoXLRCommand.set_microphone_gain(MicrophoneType.Dynamic, 56)
    assert cmd.to_dict() == {"SetMicrophoneGain": ["Dynamic", 56]}


# ---------------------------------------------------------------------------
# Scribble strips
# ---------------------------------------------------------------------------

def test_set_scribble_text() -> None:
    cmd = GoXLRCommand.set_scribble_text(FaderName.A, "Mic")
    assert cmd.to_dict() == {"SetScribbleText": ["A", "Mic"]}


def test_set_scribble_number() -> None:
    cmd = GoXLRCommand.set_scribble_number(FaderName.B, "42")
    assert cmd.to_dict() == {"SetScribbleNumber": ["B", "42"]}


def test_set_scribble_invert() -> None:
    cmd = GoXLRCommand.set_scribble_invert(FaderName.C, True)
    assert cmd.to_dict() == {"SetScribbleInvert": ["C", True]}


# ---------------------------------------------------------------------------
# General settings
# ---------------------------------------------------------------------------

def test_set_vod_mode_routable() -> None:
    cmd = GoXLRCommand.set_vod_mode(VodMode.Routable)
    assert cmd.to_dict() == {"SetVodMode": "Routable"}


def test_set_vod_mode_stream_no_music() -> None:
    cmd = GoXLRCommand.set_vod_mode(VodMode.StreamNoMusic)
    assert cmd.to_dict() == {"SetVodMode": "StreamNoMusic"}


def test_set_monitor_with_fx() -> None:
    assert GoXLRCommand.set_monitor_with_fx(False).to_dict() == {"SetMonitorWithFx": False}


def test_set_swear_button_volume_zero() -> None:
    assert GoXLRCommand.set_swear_button_volume(0).to_dict() == {"SetSwearButtonVolume": 0}


def test_set_swear_button_volume_min() -> None:
    assert GoXLRCommand.set_swear_button_volume(-34).to_dict() == {"SetSwearButtonVolume": -34}


def test_set_submix_enabled() -> None:
    assert GoXLRCommand.set_submix_enabled(True).to_dict() == {"SetSubMixEnabled": True}


def test_set_submix_volume() -> None:
    cmd = GoXLRCommand.set_submix_volume(ChannelName.Game, 200)
    assert cmd.to_dict() == {"SetSubMixVolume": ["Game", 200]}


def test_set_submix_linked() -> None:
    cmd = GoXLRCommand.set_submix_linked(ChannelName.Chat, True)
    assert cmd.to_dict() == {"SetSubMixLinked": ["Chat", True]}


def test_set_submix_output_mix() -> None:
    cmd = GoXLRCommand.set_submix_output_mix(OutputDevice.Headphones, Mix.B)
    assert cmd.to_dict() == {"SetSubMixOutputMix": ["Headphones", "B"]}


def test_set_monitor_mix() -> None:
    cmd = GoXLRCommand.set_monitor_mix(OutputDevice.Headphones)
    assert cmd.to_dict() == {"SetMonitorMix": "Headphones"}


def test_set_lock_faders() -> None:
    assert GoXLRCommand.set_lock_faders(True).to_dict() == {"SetLockFaders": True}


def test_set_mute_hold_duration() -> None:
    assert GoXLRCommand.set_mute_hold_duration(500).to_dict() == {"SetMuteHoldDuration": 500}


def test_set_element_display_mode() -> None:
    cmd = GoXLRCommand.set_element_display_mode(
        DisplayModeComponents.NoiseGate, DisplayMode.Simple
    )
    assert cmd.to_dict() == {"SetElementDisplayMode": ["NoiseGate", "Simple"]}


# ---------------------------------------------------------------------------
# Profile commands
# ---------------------------------------------------------------------------

def test_load_profile() -> None:
    cmd = GoXLRCommand.load_profile("MyProfile")
    assert cmd.to_dict() == {"LoadProfile": ["MyProfile", True]}


def test_save_profile() -> None:
    assert GoXLRCommand.save_profile().to_dict() == "SaveProfile"


def test_load_mic_profile() -> None:
    cmd = GoXLRCommand.load_mic_profile("MicProfileA")
    assert cmd.to_dict() == {"LoadMicProfile": ["MicProfileA", True]}


def test_save_profile_as() -> None:
    assert GoXLRCommand.save_profile_as("NewName").to_dict() == {"SaveProfileAs": "NewName"}


def test_rename_active_preset() -> None:
    assert GoXLRCommand.rename_active_preset("Cool FX").to_dict() == {
        "RenameActivePreset": "Cool FX"
    }


# ---------------------------------------------------------------------------
# Lighting
# ---------------------------------------------------------------------------

def test_set_button_colours() -> None:
    cmd = GoXLRCommand.set_button_colours(Button.Bleep, "FF0000", "000000")
    assert cmd.to_dict() == {"SetButtonColours": ["Bleep", "FF0000", "000000"]}


def test_set_fader_colours() -> None:
    cmd = GoXLRCommand.set_fader_colours(FaderName.A, "FFFFFF", "000000")
    assert cmd.to_dict() == {"SetFaderColours": ["A", "FFFFFF", "000000"]}


def test_set_fader_display_style() -> None:
    cmd = GoXLRCommand.set_fader_display_style(FaderName.B, FaderDisplayStyle.Meter)
    assert cmd.to_dict() == {"SetFaderDisplayStyle": ["B", "Meter"]}


def test_set_all_fader_display_style() -> None:
    cmd = GoXLRCommand.set_all_fader_display_style(FaderDisplayStyle.Gradient)
    assert cmd.to_dict() == {"SetAllFaderDisplayStyle": "Gradient"}


def test_set_global_colour() -> None:
    assert GoXLRCommand.set_global_colour("FF00FF").to_dict() == {"SetGlobalColour": "FF00FF"}


def test_set_simple_colour() -> None:
    cmd = GoXLRCommand.set_simple_colour(SimpleColourTargets.Global, "AABBCC")
    assert cmd.to_dict() == {"SetSimpleColour": ["Global", "AABBCC"]}


def test_set_button_group_colours() -> None:
    cmd = GoXLRCommand.set_button_group_colours(ButtonColourGroups.FaderMute, "FF0000", "000000")
    assert cmd.to_dict() == {"SetButtonGroupColours": ["FaderMute", "FF0000", "000000"]}


def test_set_button_off_style() -> None:
    cmd = GoXLRCommand.set_button_off_style(Button.Bleep, ButtonColourOffStyle.Dimmed, "888888")
    assert cmd.to_dict() == {"SetButtonOffStyle": ["Bleep", "Dimmed", "888888"]}


def test_set_sampler_colour() -> None:
    cmd = GoXLRCommand.set_sampler_colour(
        SamplerColourTargets.SamplerSelectA, "FF0000", "00FF00", "0000FF"
    )
    assert cmd.to_dict() == {
        "SetSamplerColour": ["SamplerSelectA", "FF0000", "00FF00", "0000FF"]
    }


def test_set_animation_mode() -> None:
    cmd = GoXLRCommand.set_animation_mode(
        AnimationMode.RetroRainbow, "FF0000", "0000FF", WaterfallDirection.Down
    )
    assert cmd.to_dict() == {
        "SetAnimationMode": ["RetroRainbow", "FF0000", "0000FF", "Down"]
    }


def test_set_all_fader_colours() -> None:
    cmd = GoXLRCommand.set_all_fader_colours("FFFFFF", "000000")
    assert cmd.to_dict() == {"SetAllFaderColours": ["FFFFFF", "000000"]}


# ---------------------------------------------------------------------------
# Unknown / edge cases
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("volume", [0, 128, 255])
def test_set_volume_valid_range(volume: int) -> None:
    cmd = GoXLRCommand.set_volume(ChannelName.Mic, volume)
    assert cmd.to_dict() == {"SetVolume": ["Mic", volume]}
