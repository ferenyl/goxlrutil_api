"""Enums and simple value types mirroring the GoXLR Utility Rust IPC types."""

from __future__ import annotations

from enum import Enum


class FaderName(str, Enum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"


class ChannelName(str, Enum):
    Mic = "Mic"
    LineIn = "LineIn"
    Console = "Console"
    System = "System"
    Game = "Game"
    Chat = "Chat"
    Sample = "Sample"
    Music = "Music"
    Headphones = "Headphones"
    MicMonitor = "MicMonitor"
    LineOut = "LineOut"


class MuteFunction(str, Enum):
    All = "All"
    ToStream = "ToStream"
    ToVoiceChat = "ToVoiceChat"
    ToPhones = "ToPhones"
    ToLineOut = "ToLineOut"


class MuteState(str, Enum):
    Unmuted = "Unmuted"
    MutedToAll = "MutedToAll"
    MutedToX = "MutedToX"


class Button(str, Enum):
    Fader1Mute = "Fader1Mute"
    Fader2Mute = "Fader2Mute"
    Fader3Mute = "Fader3Mute"
    Fader4Mute = "Fader4Mute"
    Bleep = "Bleep"
    Cough = "Cough"
    EffectSelect1 = "EffectSelect1"
    EffectSelect2 = "EffectSelect2"
    EffectSelect3 = "EffectSelect3"
    EffectSelect4 = "EffectSelect4"
    EffectSelect5 = "EffectSelect5"
    EffectSelect6 = "EffectSelect6"
    EffectFx = "EffectFx"
    EffectMegaphone = "EffectMegaphone"
    EffectRobot = "EffectRobot"
    EffectHardTune = "EffectHardTune"
    SamplerSelectA = "SamplerSelectA"
    SamplerSelectB = "SamplerSelectB"
    SamplerSelectC = "SamplerSelectC"
    SamplerTopLeft = "SamplerTopLeft"
    SamplerTopRight = "SamplerTopRight"
    SamplerBottomLeft = "SamplerBottomLeft"
    SamplerBottomRight = "SamplerBottomRight"
    SamplerClear = "SamplerClear"


class InputDevice(str, Enum):
    Microphone = "Microphone"
    Chat = "Chat"
    Music = "Music"
    Game = "Game"
    Console = "Console"
    LineIn = "LineIn"
    System = "System"
    Samples = "Samples"


class OutputDevice(str, Enum):
    Headphones = "Headphones"
    BroadcastMix = "BroadcastMix"
    LineOut = "LineOut"
    ChatMic = "ChatMic"
    Sampler = "Sampler"


class Mix(str, Enum):
    A = "A"
    B = "B"


class MicrophoneType(str, Enum):
    Dynamic = "Dynamic"
    Condenser = "Condenser"
    Jack = "Jack"


class DeviceType(str, Enum):
    Full = "Full"
    Mini = "Mini"


class EffectBankPresets(str, Enum):
    Preset1 = "Preset1"
    Preset2 = "Preset2"
    Preset3 = "Preset3"
    Preset4 = "Preset4"
    Preset5 = "Preset5"
    Preset6 = "Preset6"


class SampleBank(str, Enum):
    A = "A"
    B = "B"
    C = "C"


class SampleButtons(str, Enum):
    TopLeft = "TopLeft"
    TopRight = "TopRight"
    BottomLeft = "BottomLeft"
    BottomRight = "BottomRight"


class SamplePlaybackMode(str, Enum):
    PlayNext = "PlayNext"
    PlayStop = "PlayStop"
    PlayFade = "PlayFade"
    StopOnRelease = "StopOnRelease"
    FadeOnRelease = "FadeOnRelease"
    Loop = "Loop"


class SamplePlayOrder(str, Enum):
    Sequential = "Sequential"
    Random = "Random"


class ReverbStyle(str, Enum):
    Library = "Library"
    DarkBloom = "DarkBloom"
    MusicClub = "MusicClub"
    RealPlate = "RealPlate"
    Chapel = "Chapel"
    HockeyArena = "HockeyArena"


class EchoStyle(str, Enum):
    Quarter = "Quarter"
    Eighth = "Eighth"
    Multihead = "Multihead"
    Studio = "Studio"
    ClassicSlap = "ClassicSlap"
    MpoDelay = "MpoDelay"


class PitchStyle(str, Enum):
    Narrow = "Narrow"
    Wide = "Wide"


class GenderStyle(str, Enum):
    Narrow = "Narrow"
    Medium = "Medium"
    Wide = "Wide"


class MegaphoneStyle(str, Enum):
    Megaphone = "Megaphone"
    Radio = "Radio"
    OnThePhone = "OnThePhone"
    Overdrive = "Overdrive"
    BuzzCutt = "BuzzCutt"
    Tweed = "Tweed"


class RobotStyle(str, Enum):
    Robot1 = "Robot1"
    Robot2 = "Robot2"
    Robot3 = "Robot3"


class RobotRange(str, Enum):
    Low = "Low"
    Medium = "Medium"
    High = "High"


class HardTuneStyle(str, Enum):
    Natural = "Natural"
    Medium = "Medium"
    Hard = "Hard"


class HardTuneSource(str, Enum):
    All = "All"
    Music = "Music"
    Game = "Game"
    LineIn = "LineIn"
    System = "System"


class FaderDisplayStyle(str, Enum):
    TwoColour = "TwoColour"
    Gradient = "Gradient"
    Meter = "Meter"
    GradientMeter = "GradientMeter"


class ButtonColourOffStyle(str, Enum):
    Dimmed = "Dimmed"
    Colour2 = "Colour2"
    Dimmed2 = "Dimmed2"


class SimpleColourTargets(str, Enum):
    Global = "Global"
    Accent = "Accent"
    ScribbleBack = "ScribbleBack"


class EncoderColourTargets(str, Enum):
    Reverb = "Reverb"
    Pitch = "Pitch"
    Echo = "Echo"
    Gender = "Gender"


class SamplerColourTargets(str, Enum):
    SamplerSelectA = "SamplerSelectA"
    SamplerSelectB = "SamplerSelectB"
    SamplerSelectC = "SamplerSelectC"


class ButtonColourGroups(str, Enum):
    FaderMute = "FaderMute"
    EffectSelector = "EffectSelector"
    EffectTypes = "EffectTypes"


class AnimationMode(str, Enum):
    RetroRainbow = "RetroRainbow"
    RainbowDark = "RainbowDark"
    RainbowBright = "RainbowBright"
    Simple = "Simple"
    Ripple = "Ripple"
    None_ = "None"


class WaterfallDirection(str, Enum):
    Down = "Down"
    Up = "Up"
    Off = "Off"


class DisplayMode(str, Enum):
    Simple = "Simple"
    Advanced = "Advanced"


class DisplayModeComponents(str, Enum):
    NoiseGate = "NoiseGate"
    Equaliser = "Equaliser"
    Compressor = "Compressor"
    EqFineTune = "EqFineTune"


class EqFrequencies(str, Enum):
    Equalizer31Hz = "Equalizer31Hz"
    Equalizer63Hz = "Equalizer63Hz"
    Equalizer125Hz = "Equalizer125Hz"
    Equalizer250Hz = "Equalizer250Hz"
    Equalizer500Hz = "Equalizer500Hz"
    Equalizer1KHz = "Equalizer1KHz"
    Equalizer2KHz = "Equalizer2KHz"
    Equalizer4KHz = "Equalizer4KHz"
    Equalizer8KHz = "Equalizer8KHz"
    Equalizer16KHz = "Equalizer16KHz"


class MiniEqFrequencies(str, Enum):
    Equalizer90Hz = "Equalizer90Hz"
    Equalizer250Hz = "Equalizer250Hz"
    Equalizer500Hz = "Equalizer500Hz"
    Equalizer1KHz = "Equalizer1KHz"
    Equalizer3KHz = "Equalizer3KHz"
    Equalizer8KHz = "Equalizer8KHz"


class GateTimes(str, Enum):
    Attack10ms = "Attack10ms"
    Attack20ms = "Attack20ms"
    Attack30ms = "Attack30ms"
    Attack40ms = "Attack40ms"
    Attack50ms = "Attack50ms"
    Attack60ms = "Attack60ms"
    Attack70ms = "Attack70ms"
    Attack80ms = "Attack80ms"
    Attack90ms = "Attack90ms"
    Attack100ms = "Attack100ms"
    Attack110ms = "Attack110ms"
    Attack120ms = "Attack120ms"
    Attack130ms = "Attack130ms"
    Attack140ms = "Attack140ms"
    Attack150ms = "Attack150ms"
    Attack160ms = "Attack160ms"
    Attack170ms = "Attack170ms"
    Attack180ms = "Attack180ms"
    Attack190ms = "Attack190ms"
    Attack200ms = "Attack200ms"
    Attack250ms = "Attack250ms"
    Attack300ms = "Attack300ms"
    Attack350ms = "Attack350ms"
    Attack400ms = "Attack400ms"
    Attack450ms = "Attack450ms"
    Attack500ms = "Attack500ms"
    Attack600ms = "Attack600ms"
    Attack700ms = "Attack700ms"
    Attack800ms = "Attack800ms"
    Attack900ms = "Attack900ms"
    Attack1000ms = "Attack1000ms"
    Attack1100ms = "Attack1100ms"
    Attack1200ms = "Attack1200ms"
    Attack1300ms = "Attack1300ms"
    Attack1400ms = "Attack1400ms"
    Attack1500ms = "Attack1500ms"
    Attack1600ms = "Attack1600ms"
    Attack1700ms = "Attack1700ms"
    Attack1800ms = "Attack1800ms"
    Attack1900ms = "Attack1900ms"
    Attack2000ms = "Attack2000ms"


class CompressorAttackTime(str, Enum):
    Attack0ms = "Attack0ms"
    Attack2ms = "Attack2ms"
    Attack3ms = "Attack3ms"
    Attack4ms = "Attack4ms"
    Attack5ms = "Attack5ms"
    Attack6ms = "Attack6ms"
    Attack7ms = "Attack7ms"
    Attack8ms = "Attack8ms"
    Attack9ms = "Attack9ms"
    Attack10ms = "Attack10ms"
    Attack12ms = "Attack12ms"
    Attack14ms = "Attack14ms"
    Attack16ms = "Attack16ms"
    Attack18ms = "Attack18ms"
    Attack20ms = "Attack20ms"
    Attack23ms = "Attack23ms"
    Attack26ms = "Attack26ms"
    Attack30ms = "Attack30ms"
    Attack35ms = "Attack35ms"
    Attack40ms = "Attack40ms"


class CompressorReleaseTime(str, Enum):
    Release0ms = "Release0ms"
    Release15ms = "Release15ms"
    Release25ms = "Release25ms"
    Release35ms = "Release35ms"
    Release45ms = "Release45ms"
    Release55ms = "Release55ms"
    Release65ms = "Release65ms"
    Release75ms = "Release75ms"
    Release85ms = "Release85ms"
    Release100ms = "Release100ms"
    Release115ms = "Release115ms"
    Release140ms = "Release140ms"
    Release160ms = "Release160ms"
    Release185ms = "Release185ms"
    Release215ms = "Release215ms"
    Release250ms = "Release250ms"
    Release290ms = "Release290ms"
    Release340ms = "Release340ms"
    Release395ms = "Release395ms"
    Release458ms = "Release458ms"
    Release533ms = "Release533ms"
    Release620ms = "Release620ms"
    Release721ms = "Release721ms"
    Release838ms = "Release838ms"
    Release975ms = "Release975ms"
    Release1135ms = "Release1135ms"
    Release1320ms = "Release1320ms"
    Release1535ms = "Release1535ms"
    Release1785ms = "Release1785ms"
    Release2075ms = "Release2075ms"
    Release2415ms = "Release2415ms"


class CompressorRatio(str, Enum):
    Ratio1to1 = "Ratio1to1"
    Ratio1_1to1 = "Ratio1_1to1"
    Ratio1_2to1 = "Ratio1_2to1"
    Ratio1_4to1 = "Ratio1_4to1"
    Ratio1_6to1 = "Ratio1_6to1"
    Ratio1_8to1 = "Ratio1_8to1"
    Ratio2to1 = "Ratio2to1"
    Ratio2_5to1 = "Ratio2_5to1"
    Ratio3to1 = "Ratio3to1"
    Ratio3_5to1 = "Ratio3_5to1"
    Ratio4to1 = "Ratio4to1"
    Ratio5to1 = "Ratio5to1"
    Ratio6to1 = "Ratio6to1"
    Ratio8to1 = "Ratio8to1"
    Ratio16to1 = "Ratio16to1"
    Ratio32to1 = "Ratio32to1"


class VodMode(str, Enum):
    AnnouncerMode = "AnnouncerMode"
    NormalMode = "NormalMode"


class SubMixChannelName(str, Enum):
    Mic = "Mic"
    LineIn = "LineIn"
    Console = "Console"
    System = "System"
    Game = "Game"
    Chat = "Chat"
    Sample = "Sample"
    Music = "Music"
