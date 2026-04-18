"""Protocol response types mirroring DaemonStatus and related structs."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, cast

from goxlrutil_api.protocol.types import (
    AnimationMode,
    ButtonColourOffStyle,
    ChannelName,
    CompressorAttackTime,
    CompressorRatio,
    CompressorReleaseTime,
    DeviceType,
    DisplayMode,
    EchoStyle,
    EffectBankPresets,
    FaderDisplayStyle,
    GateTimes,
    GenderStyle,
    HardTuneSource,
    HardTuneStyle,
    MegaphoneStyle,
    MicrophoneType,
    MuteFunction,
    MuteState,
    OutputDevice,
    PitchStyle,
    ReverbStyle,
    RobotStyle,
    SampleBank,
    SamplePlaybackMode,
    SamplePlayOrder,
    VodMode,
    WaterfallDirection,
)

# ---------------------------------------------------------------------------
# Hardware
# ---------------------------------------------------------------------------

@dataclass
class VersionNumber:
    major: int
    minor: int
    patch: int
    build: int | None = None


@dataclass
class FirmwareVersions:
    firmware: VersionNumber | None = None
    fpga_count: int | None = None
    dice: VersionNumber | None = None


@dataclass
class UsbProductInformation:
    manufacturer_name: str = ""
    product_name: str = ""
    version: tuple[int, int, int] = (0, 0, 0)
    bus_number: int = 0
    address: int = 0
    identifier: str | None = None


@dataclass
class HardwareStatus:
    versions: FirmwareVersions = field(default_factory=FirmwareVersions)
    serial_number: str = ""
    manufactured_date: str = ""
    device_type: DeviceType = DeviceType.Full
    colour_way: str = "Black"
    usb_device: UsbProductInformation = field(default_factory=UsbProductInformation)


# ---------------------------------------------------------------------------
# Faders / Buttons
# ---------------------------------------------------------------------------

@dataclass
class Scribble:
    file_name: str | None = None
    bottom_text: str | None = None
    left_text: str | None = None
    inverted: bool = False


@dataclass
class FaderStatus:
    channel: ChannelName = ChannelName.Mic
    mute_type: MuteFunction = MuteFunction.All
    scribble: Scribble | None = None
    mute_state: MuteState = MuteState.Unmuted


@dataclass
class CoughButton:
    is_toggle: bool = False
    mute_type: MuteFunction = MuteFunction.All
    state: MuteState = MuteState.Unmuted


# ---------------------------------------------------------------------------
# Levels / Submix
# ---------------------------------------------------------------------------

@dataclass
class Submix:
    volume: int = 0
    linked: bool = False
    ratio: float = 0.0


@dataclass
class Submixes:
    inputs: dict[str, Submix] = field(default_factory=dict[str, Submix])
    outputs: dict[str, str] = field(default_factory=dict[str, str])


@dataclass
class Levels:
    submix_supported: bool = False
    output_monitor: OutputDevice = OutputDevice.Headphones
    volumes: dict[str, int] = field(default_factory=dict[str, int])
    submix: Submixes | None = None
    bleep: int = 0
    deess: int = 0


# ---------------------------------------------------------------------------
# Mic / EQ
# ---------------------------------------------------------------------------

@dataclass
class Equaliser:
    gain: dict[str, int] = field(default_factory=dict[str, int])
    frequency: dict[str, float] = field(default_factory=dict[str, float])


@dataclass
class EqualiserMini:
    gain: dict[str, int] = field(default_factory=dict[str, int])
    frequency: dict[str, float] = field(default_factory=dict[str, float])


@dataclass
class NoiseGate:
    threshold: int = 0
    attack: GateTimes = GateTimes.Attack10ms
    release: GateTimes = GateTimes.Attack10ms
    enabled: bool = False
    attenuation: int = 0


@dataclass
class Compressor:
    threshold: int = 0
    ratio: CompressorRatio = CompressorRatio.Ratio1to1
    attack: CompressorAttackTime = CompressorAttackTime.Attack0ms
    release: CompressorReleaseTime = CompressorReleaseTime.Release0ms
    makeup_gain: int = 0


@dataclass
class MicSettings:
    mic_type: MicrophoneType = MicrophoneType.Dynamic
    mic_gains: dict[str, int] = field(default_factory=dict[str, int])
    equaliser: Equaliser = field(default_factory=Equaliser)
    equaliser_mini: EqualiserMini = field(default_factory=EqualiserMini)
    noise_gate: NoiseGate = field(default_factory=NoiseGate)
    compressor: Compressor = field(default_factory=Compressor)


# ---------------------------------------------------------------------------
# Lighting
# ---------------------------------------------------------------------------

@dataclass
class OneColour:
    colour_one: str = "000000"


@dataclass
class TwoColours:
    colour_one: str = "000000"
    colour_two: str = "000000"


@dataclass
class ThreeColours:
    colour_one: str = "000000"
    colour_two: str = "000000"
    colour_three: str = "000000"


@dataclass
class ButtonLighting:
    off_style: ButtonColourOffStyle = ButtonColourOffStyle.Dimmed
    colours: TwoColours = field(default_factory=TwoColours)


@dataclass
class FaderLighting:
    style: FaderDisplayStyle = FaderDisplayStyle.TwoColour
    colours: TwoColours = field(default_factory=TwoColours)


@dataclass
class SamplerLighting:
    off_style: ButtonColourOffStyle = ButtonColourOffStyle.Dimmed
    colours: ThreeColours = field(default_factory=ThreeColours)


@dataclass
class AnimationLighting:
    supported: bool = False
    mode: AnimationMode = AnimationMode.None_
    mod1: int = 0
    mod2: int = 0
    waterfall_direction: WaterfallDirection = WaterfallDirection.Off


@dataclass
class Lighting:
    animation: AnimationLighting = field(default_factory=AnimationLighting)
    faders: dict[str, FaderLighting] = field(default_factory=dict[str, FaderLighting])
    buttons: dict[str, ButtonLighting] = field(default_factory=dict[str, ButtonLighting])
    simple: dict[str, OneColour] = field(default_factory=dict[str, OneColour])
    sampler: dict[str, SamplerLighting] = field(default_factory=dict[str, SamplerLighting])
    encoders: dict[str, ThreeColours] = field(default_factory=dict[str, ThreeColours])


# ---------------------------------------------------------------------------
# Effects
# ---------------------------------------------------------------------------

@dataclass
class Reverb:
    style: ReverbStyle = ReverbStyle.Library
    amount: int = 0
    decay: int = 0
    early_level: int = 0
    tail_level: int = 0
    pre_delay: int = 0
    lo_colour: int = 0
    hi_colour: int = 0
    hi_factor: int = 0
    diffuse: int = 0
    mod_speed: int = 0
    mod_depth: int = 0
    raw_encoder: int = 0


@dataclass
class Echo:
    style: EchoStyle = EchoStyle.Quarter
    amount: int = 0
    feedback: int = 0
    tempo: int = 0
    delay_left: int = 0
    delay_right: int = 0
    feedback_left: int = 0
    feedback_right: int = 0
    feedback_xfb_l_to_r: int = 0
    feedback_xfb_r_to_l: int = 0
    raw_encoder: int = 0


@dataclass
class Pitch:
    style: PitchStyle = PitchStyle.Narrow
    amount: int = 0
    character: int = 0
    raw_encoder: int = 0


@dataclass
class Gender:
    style: GenderStyle = GenderStyle.Narrow
    amount: int = 0
    raw_encoder: int = 0


@dataclass
class Megaphone:
    is_enabled: bool = False
    style: MegaphoneStyle = MegaphoneStyle.Megaphone
    amount: int = 0
    post_gain: int = 0


@dataclass
class Robot:
    is_enabled: bool = False
    style: RobotStyle = RobotStyle.Robot1
    low_gain: int = 0
    low_freq: int = 0
    low_width: int = 0
    mid_gain: int = 0
    mid_freq: int = 0
    mid_width: int = 0
    high_gain: int = 0
    high_freq: int = 0
    high_width: int = 0
    waveform: int = 0
    pulse_width: int = 0
    threshold: int = 0
    dry_mix: int = 0


@dataclass
class HardTune:
    is_enabled: bool = False
    style: HardTuneStyle = HardTuneStyle.Natural
    amount: int = 0
    rate: int = 0
    window: int = 0
    source: HardTuneSource = HardTuneSource.All


@dataclass
class ActiveEffects:
    reverb: Reverb = field(default_factory=Reverb)
    echo: Echo = field(default_factory=Echo)
    pitch: Pitch = field(default_factory=Pitch)
    gender: Gender = field(default_factory=Gender)
    megaphone: Megaphone = field(default_factory=Megaphone)
    robot: Robot = field(default_factory=Robot)
    hard_tune: HardTune = field(default_factory=HardTune)


@dataclass
class Effects:
    is_enabled: bool = False
    active_preset: EffectBankPresets = EffectBankPresets.Preset1
    preset_names: dict[str, str] = field(default_factory=dict[str, str])
    current: ActiveEffects = field(default_factory=ActiveEffects)


# ---------------------------------------------------------------------------
# Sampler
# ---------------------------------------------------------------------------

@dataclass
class Sample:
    name: str = ""
    start_pct: float = 0.0
    stop_pct: float = 1.0


@dataclass
class SamplerButton:
    function: SamplePlaybackMode = SamplePlaybackMode.PlayNext
    order: SamplePlayOrder = SamplePlayOrder.Sequential
    samples: list[Sample] = field(default_factory=list[Sample])
    is_playing: bool = False
    is_recording: bool = False


@dataclass
class SampleProcessState:
    progress: int | None = None
    last_error: str | None = None


@dataclass
class Sampler:
    processing_state: SampleProcessState = field(default_factory=SampleProcessState)
    active_bank: SampleBank = SampleBank.A
    clear_active: bool = False
    record_buffer: int = 0
    banks: dict[str, dict[str, SamplerButton]] = field(
        default_factory=dict[str, dict[str, SamplerButton]]
    )


# ---------------------------------------------------------------------------
# Settings / Display
# ---------------------------------------------------------------------------

@dataclass
class Display:
    gate: DisplayMode = DisplayMode.Simple
    compressor: DisplayMode = DisplayMode.Simple
    equaliser: DisplayMode = DisplayMode.Simple
    equaliser_fine: DisplayMode = DisplayMode.Simple


@dataclass
class Settings:
    display: Display = field(default_factory=Display)
    mute_hold_duration: int = 500
    vc_mute_also_mute_cm: bool = False
    enable_monitor_with_fx: bool = False
    reset_sampler_on_clear: bool = False
    lock_faders: bool = False
    fade_duration: int = 0
    vod_mode: VodMode = VodMode.Routable


# ---------------------------------------------------------------------------
# MixerStatus
# ---------------------------------------------------------------------------

@dataclass
class MixerStatus:
    hardware: HardwareStatus = field(default_factory=HardwareStatus)
    shutdown_commands: list[Any] = field(default_factory=list[Any])
    sleep_commands: list[Any] = field(default_factory=list[Any])
    wake_commands: list[Any] = field(default_factory=list[Any])
    fader_status: dict[str, FaderStatus] = field(default_factory=dict[str, FaderStatus])
    mic_status: MicSettings = field(default_factory=MicSettings)
    levels: Levels = field(default_factory=Levels)
    router: dict[str, dict[str, bool]] = field(default_factory=dict[str, dict[str, bool]])
    cough_button: CoughButton = field(default_factory=CoughButton)
    lighting: Lighting = field(default_factory=Lighting)
    effects: Effects | None = None
    sampler: Sampler | None = None
    settings: Settings = field(default_factory=Settings)
    button_down: dict[str, bool] = field(default_factory=dict[str, bool])
    profile_name: str = ""
    mic_profile_name: str = ""


# ---------------------------------------------------------------------------
# Daemon-level status
# ---------------------------------------------------------------------------

@dataclass
class HttpSettings:
    enabled: bool = False
    bind_address: str = "0.0.0.0"
    cors_enabled: bool = False
    port: int = 14564


@dataclass
class DaemonConfig:
    http_settings: HttpSettings = field(default_factory=HttpSettings)
    daemon_version: str = ""
    allow_network_access: bool = False
    log_level: str = "Info"
    show_tray_icon: bool = True
    tts_enabled: bool | None = None
    autostart_enabled: bool = False
    open_ui_on_launch: bool = False
    platform: str = ""


@dataclass
class Paths:
    profile_directory: str = ""
    mic_profile_directory: str = ""
    samples_directory: str = ""
    presets_directory: str = ""
    icons_directory: str = ""
    logs_directory: str = ""


@dataclass
class SampleFile:
    name: str = ""
    gain_pct: int = 100


@dataclass
class Files:
    profiles: list[str] = field(default_factory=list[str])
    mic_profiles: list[str] = field(default_factory=list[str])
    presets: list[str] = field(default_factory=list[str])
    samples: dict[str, SampleFile] = field(default_factory=dict[str, SampleFile])
    icons: list[str] = field(default_factory=list[str])


@dataclass
class DaemonStatus:
    config: DaemonConfig = field(default_factory=DaemonConfig)
    firmware: dict[str, Any] = field(default_factory=dict[str, Any])
    mixers: dict[str, MixerStatus] = field(default_factory=dict[str, MixerStatus])
    paths: Paths = field(default_factory=Paths)
    files: Files = field(default_factory=Files)


# ---------------------------------------------------------------------------
# DaemonResponse
# ---------------------------------------------------------------------------

@dataclass
class DaemonResponse:
    """Parsed response from the daemon."""

    ok: bool = False
    error: str | None = None
    status: DaemonStatus | None = None
    raw_status: dict[str, Any] | None = None
    patch: list[Any] | None = None
    mic_level: float | None = None

    @staticmethod
    def from_dict(data: object) -> DaemonResponse:
        d_any: Any = data
        if d_any == "Ok":
            return DaemonResponse(ok=True)
        if isinstance(d_any, dict):
            d: dict[str, Any] = cast(dict[str, Any], d_any)
            if "Error" in d:
                return DaemonResponse(error=str(d["Error"]))
            if "Status" in d:
                raw: dict[str, Any] = cast(dict[str, Any], d["Status"])
                return DaemonResponse(status=parse_status(raw), raw_status=raw)
            if "Patch" in d:
                return DaemonResponse(patch=list(cast(list[Any], d["Patch"])))
            if "MicLevel" in d:
                return DaemonResponse(mic_level=float(d["MicLevel"]))
        return DaemonResponse(error=f"Unknown response: {data!r}")


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

def parse_status(raw: dict[str, Any]) -> DaemonStatus:
    status = DaemonStatus()
    if "config" in raw:
        cfg = raw["config"]
        http = cfg.get("http_settings", {})
        status.config = DaemonConfig(
            http_settings=HttpSettings(
                enabled=http.get("enabled", False),
                bind_address=http.get("bind_address", "0.0.0.0"),
                cors_enabled=http.get("cors_enabled", False),
                port=http.get("port", 14564),
            ),
            daemon_version=cfg.get("daemon_version", ""),
            allow_network_access=cfg.get("allow_network_access", False),
            log_level=cfg.get("log_level", "Info"),
            show_tray_icon=cfg.get("show_tray_icon", True),
            tts_enabled=cfg.get("tts_enabled"),
            autostart_enabled=cfg.get("autostart_enabled", False),
            open_ui_on_launch=cfg.get("open_ui_on_launch", False),
            platform=cfg.get("platform", ""),
        )
    if "mixers" in raw:
        for serial, mixer_raw in raw["mixers"].items():
            status.mixers[serial] = _parse_mixer(mixer_raw)
    if "paths" in raw:
        p = raw["paths"]
        status.paths = Paths(
            profile_directory=p.get("profile_directory", ""),
            mic_profile_directory=p.get("mic_profile_directory", ""),
            samples_directory=p.get("samples_directory", ""),
            presets_directory=p.get("presets_directory", ""),
            icons_directory=p.get("icons_directory", ""),
            logs_directory=p.get("logs_directory", ""),
        )
    if "files" in raw:
        f = raw["files"]
        status.files = Files(
            profiles=f.get("profiles", []),
            mic_profiles=f.get("mic_profiles", []),
            presets=f.get("presets", []),
            icons=f.get("icons", []),
            samples={
                k: SampleFile(name=v.get("name", k), gain_pct=v.get("gain_pct", 100))
                for k, v in f.get("samples", {}).items()
            },
        )
    return status


def _parse_mixer(raw: dict[str, Any]) -> MixerStatus:
    mixer = MixerStatus()

    hw = raw.get("hardware", {})
    mixer.hardware = HardwareStatus(
        serial_number=hw.get("serial_number", ""),
        manufactured_date=hw.get("manufactured_date", ""),
        device_type=DeviceType(hw.get("device_type", "Full")),
        colour_way=hw.get("colour_way", "Black"),
    )

    for fname, fraw in raw.get("fader_status", {}).items():
        mixer.fader_status[fname] = FaderStatus(
            channel=ChannelName(fraw.get("channel", "Mic")),
            mute_type=MuteFunction(fraw.get("mute_type", "All")),
            mute_state=MuteState(fraw.get("mute_state", "Unmuted")),
        )

    lvl = raw.get("levels", {})
    mixer.levels = Levels(
        submix_supported=lvl.get("submix_supported", False),
        output_monitor=OutputDevice(lvl.get("output_monitor", "Headphones")),
        volumes=lvl.get("volumes", {}),
        bleep=lvl.get("bleep", 0),
        deess=lvl.get("deess", 0),
    )

    cb = raw.get("cough_button", {})
    mixer.cough_button = CoughButton(
        is_toggle=cb.get("is_toggle", False),
        mute_type=MuteFunction(cb.get("mute_type", "All")),
        state=MuteState(cb.get("state", "Unmuted")),
    )

    mixer.profile_name = raw.get("profile_name", "")
    mixer.mic_profile_name = raw.get("mic_profile_name", "")
    mixer.button_down = raw.get("button_down", {})
    mixer.router = raw.get("router", {})

    eraw = raw.get("effects")
    if eraw is not None:
        cur = eraw.get("current", {})
        mega = cur.get("megaphone", {})
        robot = cur.get("robot", {})
        ht = cur.get("hard_tune", {})
        mixer.effects = Effects(
            is_enabled=eraw.get("is_enabled", False),
            active_preset=EffectBankPresets(
                eraw.get("active_preset", "Preset1")
            ),
            preset_names=eraw.get("preset_names", {}),
            current=ActiveEffects(
                megaphone=Megaphone(
                    is_enabled=mega.get("is_enabled", False),
                    style=MegaphoneStyle(mega.get("style", "Megaphone")),
                    amount=mega.get("amount", 0),
                    post_gain=mega.get("post_gain", 0),
                ),
                robot=Robot(
                    is_enabled=robot.get("is_enabled", False),
                    style=RobotStyle(robot.get("style", "Robot1")),
                    low_gain=robot.get("low_gain", 0),
                    low_freq=robot.get("low_freq", 0),
                    low_width=robot.get("low_width", 0),
                    mid_gain=robot.get("mid_gain", 0),
                    mid_freq=robot.get("mid_freq", 0),
                    mid_width=robot.get("mid_width", 0),
                    high_gain=robot.get("high_gain", 0),
                    high_freq=robot.get("high_freq", 0),
                    high_width=robot.get("high_width", 0),
                    waveform=robot.get("waveform", 0),
                    pulse_width=robot.get("pulse_width", 0),
                    threshold=robot.get("threshold", 0),
                    dry_mix=robot.get("dry_mix", 0),
                ),
                hard_tune=HardTune(
                    is_enabled=ht.get("is_enabled", False),
                    style=HardTuneStyle(ht.get("style", "Natural")),
                    amount=ht.get("amount", 0),
                    rate=ht.get("rate", 0),
                    window=ht.get("window", 0),
                    source=HardTuneSource(ht.get("source", "All")),
                ),
            ),
        )

    return mixer
