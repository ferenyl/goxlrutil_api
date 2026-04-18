"""Demo FastAPI webapp for goxlrutil_api.

Provides a minimal UI to:
  - See connection status
  - Inspect mixer state (read-only)
  - Adjust volume and mute faders (write, reversible)

Start with:
    uvicorn apps.demo_webapp.main:app --reload
"""

from __future__ import annotations

import logging
import os
from collections import deque
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, suppress
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from goxlrutil_api import GoXLRClient, UnixSocketTransport, WebSocketTransport
from goxlrutil_api.colour import Colour
from goxlrutil_api.events import ButtonEvent
from goxlrutil_api.exceptions import GoXLRError
from goxlrutil_api.protocol.commands import GoXLRCommand
from goxlrutil_api.protocol.responses import DaemonStatus
from goxlrutil_api.protocol.types import (
    Button,
    ChannelName,
    CompressorAttackTime,
    CompressorRatio,
    CompressorReleaseTime,
    EchoStyle,
    EffectBankPresets,
    EqFrequencies,
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
    VodMode,
)

_log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Transport selection: prefer WebSocket for live updates, fall back to socket
# ---------------------------------------------------------------------------
_USE_WS = os.getenv("GOXLR_USE_WS", "1") == "1"
_WS_URL = os.getenv("GOXLR_WS_URL", "ws://localhost:14564/api/websocket")

_client: GoXLRClient | None = None
_status: DaemonStatus | None = None
_connected = False

# Up to 50 most recent button events per mixer serial
_button_log: dict[str, deque[ButtonEvent]] = {}
_BUTTON_LOG_MAX = 50


async def _on_button_event(event: ButtonEvent) -> None:
    log = _button_log.setdefault(event.serial, deque(maxlen=_BUTTON_LOG_MAX))
    log.appendleft(event)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:  # type: ignore[type-arg]
    global _client, _status, _connected
    transport = WebSocketTransport(_WS_URL) if _USE_WS else UnixSocketTransport()
    _client = GoXLRClient(transport, on_button_event=_on_button_event)
    try:
        await _client.__aenter__()
        _status = await _client.get_status()
        _connected = True
        _log.info("Connected to GoXLR daemon")
    except GoXLRError as exc:
        _log.warning("Could not connect to GoXLR daemon: %s", exc)
        _connected = False
    yield
    if _client is not None:
        await _client.__aexit__(None, None, None)


app = FastAPI(title="GoXLR Demo", lifespan=lifespan)

_BASE = Path(__file__).parent
templates = Jinja2Templates(directory=_BASE / "templates")
app.mount("/static", StaticFiles(directory=str(_BASE / "static")), name="static")


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    global _status
    if _client and _connected:
        with suppress(GoXLRError):
            _status = await _client.get_status()
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "connected": _connected,
            "status": _status,
            "channel_names": [c.value for c in ChannelName],
            "fader_names": [f.value for f in FaderName],
            "effect_presets": [p.value for p in EffectBankPresets],
            "sample_banks": [b.value for b in SampleBank],
            "sample_buttons": [b.value for b in SampleButtons],
            "profiles": _status.files.profiles if _status else [],
            "mic_profiles": _status.files.mic_profiles if _status else [],
            "eq_freqs": [f.value for f in EqFrequencies],
            "mini_eq_freqs": [f.value for f in MiniEqFrequencies],
            "gate_times": [t.value for t in GateTimes],
            "compressor_ratios": [r.value for r in CompressorRatio],
            "compressor_attacks": [a.value for a in CompressorAttackTime],
            "compressor_releases": [r.value for r in CompressorReleaseTime],
            "megaphone_styles": [s.value for s in MegaphoneStyle],
            "robot_styles": [s.value for s in RobotStyle],
            "robot_ranges": [r.value for r in RobotRange],
            "hardtune_styles": [s.value for s in HardTuneStyle],
            "hardtune_sources": [s.value for s in HardTuneSource],
            "mute_functions": [f.value for f in MuteFunction],
            "mix_values": [m.value for m in Mix],
            "output_devices": [o.value for o in OutputDevice],
        },
    )


@app.post("/api/volume/{serial}/{channel}/{volume}")
async def set_volume(serial: str, channel: str, volume: int) -> dict[str, Any]:
    _require_connected()
    if volume < 0 or volume > 255:
        raise HTTPException(status_code=422, detail="Volume must be 0-255")
    try:
        ch = ChannelName(channel)
    except ValueError:
        raise HTTPException(status_code=422, detail=f"Unknown channel: {channel}") from None
    assert _client is not None
    await _client.command(serial, GoXLRCommand.set_volume(ch, volume))
    return {"ok": True, "channel": channel, "volume": volume}


@app.post("/api/mute/{serial}/{fader}/{state}", response_class=HTMLResponse)
async def set_mute(request: Request, serial: str, fader: str, state: str) -> HTMLResponse:
    _require_connected()
    try:
        f = FaderName(fader)
        s = MuteState(state)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    assert _client is not None
    await _client.command(serial, GoXLRCommand.set_fader_mute_state(f, s))
    status = await _client.get_status()
    mixer = status.mixers.get(serial)
    fs = mixer.fader_status.get(fader) if mixer else None
    return templates.TemplateResponse(
        request,
        "_fader_block.html",
        {"serial": serial, "fname": fader, "fs": fs},
    )


async def _render_effects(request: Request, serial: str) -> HTMLResponse:
    """Re-fetch state and render the effects partial block."""
    assert _client is not None
    s = await _client.get_status()
    mixer = s.mixers.get(serial)
    return templates.TemplateResponse(
        request,
        "_effects_block.html",
        {
            "serial": serial,
            "mixer": mixer,
            "effect_presets": [p.value for p in EffectBankPresets],
        },
    )


@app.post("/api/fx/{serial}/toggle", response_class=HTMLResponse)
async def toggle_fx(request: Request, serial: str) -> HTMLResponse:
    _require_connected()
    assert _client is not None
    await _client.toggle_fx(serial)
    return await _render_effects(request, serial)


@app.post("/api/effect/preset/{serial}/{preset}", response_class=HTMLResponse)
async def set_effect_preset(request: Request, serial: str, preset: str) -> HTMLResponse:
    _require_connected()
    assert _client is not None
    try:
        p = EffectBankPresets(preset)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    await _client.set_active_effect_preset(serial, p)
    return await _render_effects(request, serial)


@app.post("/api/effect/megaphone/{serial}/toggle", response_class=HTMLResponse)
async def toggle_megaphone(request: Request, serial: str) -> HTMLResponse:
    _require_connected()
    assert _client is not None
    await _client.toggle_megaphone(serial)
    return await _render_effects(request, serial)


@app.post("/api/effect/robot/{serial}/toggle", response_class=HTMLResponse)
async def toggle_robot(request: Request, serial: str) -> HTMLResponse:
    _require_connected()
    assert _client is not None
    await _client.toggle_robot(serial)
    return await _render_effects(request, serial)


@app.post("/api/effect/hardtune/{serial}/toggle", response_class=HTMLResponse)
async def toggle_hard_tune(request: Request, serial: str) -> HTMLResponse:
    _require_connected()
    assert _client is not None
    await _client.toggle_hard_tune(serial)
    return await _render_effects(request, serial)


@app.post("/api/sampler/play/{serial}/{bank}/{button}")
async def play_sample(serial: str, bank: str, button: str) -> dict[str, Any]:
    _require_connected()
    assert _client is not None
    try:
        b = SampleBank(bank)
        btn = SampleButtons(button)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    await _client.play_sample(serial, b, btn)
    return {"ok": True, "bank": bank, "button": button}


@app.post("/api/sampler/stop/{serial}/{bank}/{button}")
async def stop_sample(serial: str, bank: str, button: str) -> dict[str, Any]:
    _require_connected()
    assert _client is not None
    try:
        b = SampleBank(bank)
        btn = SampleButtons(button)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    await _client.stop_sample(serial, b, btn)
    return {"ok": True, "bank": bank, "button": button}


@app.get("/api/status")
async def api_status() -> dict[str, Any]:
    _require_connected()
    assert _client is not None
    s = await _client.get_status()
    mixers_out = {}
    for serial, mixer in s.mixers.items():
        mixers_out[serial] = {
            "device_type": mixer.hardware.device_type.value,
            "profile": mixer.profile_name,
            "volumes": mixer.levels.volumes,
            "faders": {
                fname: {
                    "channel": fs.channel.value,
                    "mute_state": fs.mute_state.value,
                }
                for fname, fs in mixer.fader_status.items()
            },
        }
    return {"connected": True, "mixers": mixers_out}


@app.get("/partial/volumes/{serial}", response_class=HTMLResponse)
async def partial_volumes(request: Request, serial: str) -> HTMLResponse:
    """Return just the volume rows for one mixer – used for HTMX polling."""
    _require_connected()
    assert _client is not None
    s = await _client.get_status()
    mixer = s.mixers.get(serial)
    return templates.TemplateResponse(
        request,
        "_volume_rows.html",
        {"serial": serial, "mixer": mixer},
    )


@app.get("/partial/faders/{serial}", response_class=HTMLResponse)
async def partial_faders(request: Request, serial: str) -> HTMLResponse:
    """Return all fader blocks for one mixer – used for HTMX polling."""
    _require_connected()
    assert _client is not None
    s = await _client.get_status()
    mixer = s.mixers.get(serial)
    fader_names = [f.value for f in FaderName]
    return templates.TemplateResponse(
        request,
        "_fader_rows.html",
        {"serial": serial, "mixer": mixer, "fader_names": fader_names},
    )


@app.get("/partial/button-log/{serial}", response_class=HTMLResponse)
async def partial_button_log(request: Request, serial: str) -> HTMLResponse:
    """Return the recent button event log for one mixer – used for HTMX polling."""
    events = list(_button_log.get(serial, []))
    return templates.TemplateResponse(
        request,
        "_button_log.html",
        {"serial": serial, "events": events},
    )


@app.get("/partial/effects/{serial}", response_class=HTMLResponse)
async def partial_effects(request: Request, serial: str) -> HTMLResponse:
    """Return the effects section for one mixer – used for HTMX polling."""
    _require_connected()
    assert _client is not None
    s = await _client.get_status()
    mixer = s.mixers.get(serial)
    return templates.TemplateResponse(
        request,
        "_effects_block.html",
        {
            "serial": serial,
            "mixer": mixer,
            "effect_presets": [p.value for p in EffectBankPresets],
        },
    )


@app.get("/partial/profiles/{serial}", response_class=HTMLResponse)
async def partial_profiles(request: Request, serial: str) -> HTMLResponse:
    """Return the profile selector for one mixer – used for HTMX polling."""
    _require_connected()
    assert _client is not None
    s = await _client.get_status()
    mixer = s.mixers.get(serial)
    return templates.TemplateResponse(
        request,
        "_profile_select.html",
        {
            "serial": serial,
            "profiles": s.files.profiles,
            "mic_profiles": s.files.mic_profiles,
            "current_profile": mixer.profile_name if mixer else "",
            "current_mic_profile": mixer.mic_profile_name if mixer else "",
        },
    )


@app.post("/api/profile/{serial}/{name}")
async def load_profile(serial: str, name: str) -> dict[str, Any]:
    """Load a profile by name."""
    _require_connected()
    assert _client is not None
    await _client.load_profile(serial, name)
    return {"ok": True, "profile": name}


@app.post("/api/mic-profile/{serial}/{name}")
async def load_mic_profile(serial: str, name: str) -> dict[str, Any]:
    """Load a mic profile by name."""
    _require_connected()
    assert _client is not None
    await _client.load_mic_profile(serial, name)
    return {"ok": True, "mic_profile": name}


@app.post("/api/colour/global/{serial}/{colour}")
async def set_global_colour(serial: str, colour: str) -> dict[str, Any]:
    """Set the global accent colour (hex RRGGBB, no #)."""
    _require_connected()
    assert _client is not None
    try:
        c = Colour.from_hex(colour)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    await _client.set_global_colour(serial, c)
    return {"ok": True, "colour": str(c)}


@app.post("/api/colour/button/{serial}/{button}/{colour_on}")
async def set_button_colour(serial: str, button: str, colour_on: str) -> dict[str, Any]:
    """Set the active LED colour for a button (hex RRGGBB)."""
    _require_connected()
    assert _client is not None
    try:
        btn = Button(button)
        c = Colour.from_hex(colour_on)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    await _client.set_button_colour(serial, btn, c)
    return {"ok": True, "button": button, "colour": str(c)}


@app.post("/api/colour/fader/{serial}/{fader}/{colour_top}/{colour_bottom}")
async def set_fader_colour(
    serial: str, fader: str, colour_top: str, colour_bottom: str
) -> dict[str, Any]:
    """Set the two LED colours for a fader strip."""
    _require_connected()
    assert _client is not None
    try:
        f = FaderName(fader)
        ct = Colour.from_hex(colour_top)
        cb = Colour.from_hex(colour_bottom)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    await _client.set_fader_colour(serial, f, ct, cb)
    return {"ok": True, "fader": fader, "colour_top": str(ct), "colour_bottom": str(cb)}


def _require_connected() -> None:
    if not _connected or _client is None:
        raise HTTPException(status_code=503, detail="Not connected to GoXLR daemon")


# ---------------------------------------------------------------------------
# Fader / routing / misc API
# ---------------------------------------------------------------------------

@app.post("/api/fader/{serial}/{fader}/assign/{channel}")
async def set_fader_channel(serial: str, fader: str, channel: str) -> dict[str, Any]:
    """Assign a channel to a fader slot."""
    _require_connected()
    assert _client is not None
    try:
        f = FaderName(fader)
        ch = ChannelName(channel)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    await _client.set_fader(serial, f, ch)
    return {"ok": True, "fader": fader, "channel": channel}


@app.post("/api/fader/{serial}/{fader}/mute-function/{mf}")
async def set_fader_mute_function(serial: str, fader: str, mf: str) -> dict[str, Any]:
    """Set the mute function for a fader button."""
    _require_connected()
    assert _client is not None
    try:
        f = FaderName(fader)
        mute_fn = MuteFunction(mf)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    await _client.set_fader_mute_function(serial, f, mute_fn)
    return {"ok": True, "fader": fader, "mute_function": mf}


@app.post("/api/cough/{serial}/{state}")
async def set_cough_mute_state(serial: str, state: str) -> dict[str, Any]:
    """Set the cough button mute state."""
    _require_connected()
    assert _client is not None
    try:
        ms = MuteState(state)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    await _client.set_cough_mute_state(serial, ms)
    return {"ok": True, "state": state}


@app.post("/api/router/{serial}/{input}/{output}/{enabled}")
async def set_router(
    serial: str, input: str, output: str, enabled: bool
) -> dict[str, Any]:
    """Enable or disable a routing matrix cross-point."""
    _require_connected()
    assert _client is not None
    try:
        inp = InputDevice(input)
        out = OutputDevice(output)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    await _client.set_router(serial, inp, out, enabled)
    return {"ok": True, "input": input, "output": output, "enabled": enabled}


@app.get("/partial/router/{serial}", response_class=HTMLResponse)
async def partial_router(request: Request, serial: str) -> HTMLResponse:
    """Routing matrix partial for HTMX polling."""
    _require_connected()
    assert _client is not None
    s = await _client.get_status()
    mixer = s.mixers.get(serial)
    router = mixer.router if mixer else {}
    return templates.TemplateResponse(
        request,
        "_router.html",
        {
            "serial": serial,
            "router": router,
            "inputs": [i.value for i in InputDevice],
            "outputs": [o.value for o in OutputDevice],
        },
    )


@app.post("/api/profile/{serial}/save")
async def save_profile(serial: str) -> dict[str, Any]:
    """Save the current settings to the active profile."""
    _require_connected()
    assert _client is not None
    await _client.save_profile(serial)
    return {"ok": True}


# ---------------------------------------------------------------------------
# Effect parameters
# ---------------------------------------------------------------------------

@app.post("/api/effects/{serial}/reverb/style/{style}")
async def set_reverb_style(serial: str, style: str) -> dict[str, Any]:
    _require_connected()
    assert _client is not None
    try:
        s = ReverbStyle(style)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    await _client.set_reverb_style(serial, s)
    return {"ok": True, "style": style}


@app.post("/api/effects/{serial}/reverb/amount/{amount}")
async def set_reverb_amount(serial: str, amount: int) -> dict[str, Any]:
    _require_connected()
    assert _client is not None
    await _client.set_reverb_amount(serial, amount)
    return {"ok": True, "amount": amount}


@app.post("/api/effects/{serial}/echo/style/{style}")
async def set_echo_style(serial: str, style: str) -> dict[str, Any]:
    _require_connected()
    assert _client is not None
    try:
        s = EchoStyle(style)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    await _client.set_echo_style(serial, s)
    return {"ok": True, "style": style}


@app.post("/api/effects/{serial}/echo/amount/{amount}")
async def set_echo_amount(serial: str, amount: int) -> dict[str, Any]:
    _require_connected()
    assert _client is not None
    await _client.set_echo_amount(serial, amount)
    return {"ok": True, "amount": amount}


@app.post("/api/effects/{serial}/pitch/style/{style}")
async def set_pitch_style(serial: str, style: str) -> dict[str, Any]:
    _require_connected()
    assert _client is not None
    try:
        s = PitchStyle(style)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    await _client.set_pitch_style(serial, s)
    return {"ok": True, "style": style}


@app.post("/api/effects/{serial}/pitch/amount/{amount}")
async def set_pitch_amount(serial: str, amount: int) -> dict[str, Any]:
    _require_connected()
    assert _client is not None
    await _client.set_pitch_amount(serial, amount)
    return {"ok": True, "amount": amount}


@app.post("/api/effects/{serial}/gender/style/{style}")
async def set_gender_style(serial: str, style: str) -> dict[str, Any]:
    _require_connected()
    assert _client is not None
    try:
        s = GenderStyle(style)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    await _client.set_gender_style(serial, s)
    return {"ok": True, "style": style}


@app.post("/api/effects/{serial}/gender/amount/{amount}")
async def set_gender_amount(serial: str, amount: int) -> dict[str, Any]:
    _require_connected()
    assert _client is not None
    await _client.set_gender_amount(serial, amount)
    return {"ok": True, "amount": amount}


@app.get("/partial/effect-params/{serial}", response_class=HTMLResponse)
async def partial_effect_params(request: Request, serial: str) -> HTMLResponse:
    """Effect parameters partial for HTMX polling."""
    _require_connected()
    assert _client is not None
    s = await _client.get_status()
    mixer = s.mixers.get(serial)
    effects = mixer.effects if mixer else None
    return templates.TemplateResponse(
        request,
        "_effect_params.html",
        {
            "serial": serial,
            "effects": effects,
            "reverb_styles": [v.value for v in ReverbStyle],
            "echo_styles": [v.value for v in EchoStyle],
            "pitch_styles": [v.value for v in PitchStyle],
            "gender_styles": [v.value for v in GenderStyle],
        },
    )


# ---------------------------------------------------------------------------
# Mic settings
# ---------------------------------------------------------------------------

@app.post("/api/mic/{serial}/type/{mic_type}")
async def set_mic_type(serial: str, mic_type: str) -> dict[str, Any]:
    """Set the microphone type."""
    _require_connected()
    assert _client is not None
    try:
        mt = MicrophoneType(mic_type)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    await _client.set_microphone_type(serial, mt)
    return {"ok": True, "mic_type": mic_type}


@app.post("/api/mic/{serial}/gate/threshold/{threshold}")
async def set_gate_threshold(serial: str, threshold: int) -> dict[str, Any]:
    """Set the noise gate threshold (-59–0 dB)."""
    _require_connected()
    assert _client is not None
    await _client.set_gate_threshold(serial, threshold)
    return {"ok": True, "threshold": threshold}


@app.post("/api/mic/{serial}/gate/active/{active}")
async def set_gate_active(serial: str, active: bool) -> dict[str, Any]:
    """Enable or disable the noise gate."""
    _require_connected()
    assert _client is not None
    await _client.set_gate_active(serial, active)
    return {"ok": True, "active": active}


@app.get("/partial/mic-settings/{serial}", response_class=HTMLResponse)
async def partial_mic_settings(request: Request, serial: str) -> HTMLResponse:
    """Mic settings partial for HTMX polling."""
    _require_connected()
    assert _client is not None
    s = await _client.get_status()
    mixer = s.mixers.get(serial)
    mic = mixer.mic_status if mixer else None
    return templates.TemplateResponse(
        request,
        "_mic_settings.html",
        {
            "serial": serial,
            "mic": mic,
            "mic_types": [t.value for t in MicrophoneType],
        },
    )


# ---------------------------------------------------------------------------
# Mix / monitor / submix
# ---------------------------------------------------------------------------

@app.post("/api/monitor-with-fx/{serial}/{enabled}")
async def set_monitor_with_fx(serial: str, enabled: bool) -> dict[str, Any]:
    """Route monitor through FX or bypass."""
    _require_connected()
    assert _client is not None
    await _client.set_monitor_with_fx(serial, enabled)
    return {"ok": True, "enabled": enabled}


@app.post("/api/vod-mode/{serial}/{mode}")
async def set_vod_mode(serial: str, mode: str) -> dict[str, Any]:
    """Set the VOD mode."""
    _require_connected()
    assert _client is not None
    try:
        vm = VodMode(mode)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    await _client.set_vod_mode(serial, vm)
    return {"ok": True, "mode": mode}


@app.post("/api/swear-volume/{serial}/{volume}")
async def set_swear_volume(serial: str, volume: int) -> dict[str, Any]:
    """Set the swear/bleep button duck volume."""
    _require_connected()
    assert _client is not None
    await _client.set_swear_button_volume(serial, volume)
    return {"ok": True, "volume": volume}


@app.post("/api/submix/{serial}/enabled/{enabled}")
async def set_submix_enabled(serial: str, enabled: bool) -> dict[str, Any]:
    """Enable or disable the submix system."""
    _require_connected()
    assert _client is not None
    await _client.set_submix_enabled(serial, enabled)
    return {"ok": True, "enabled": enabled}


@app.post("/api/submix/{serial}/volume/{channel}/{volume}")
async def set_submix_volume(serial: str, channel: str, volume: int) -> dict[str, Any]:
    """Set the submix B volume for a channel."""
    _require_connected()
    assert _client is not None
    try:
        ch = ChannelName(channel)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    await _client.set_submix_volume(serial, ch, volume)
    return {"ok": True, "channel": channel, "volume": volume}


@app.post("/api/monitor-mix/{serial}/{output}")
async def set_monitor_mix(serial: str, output: str) -> dict[str, Any]:
    """Set the headphone monitor mix source."""
    _require_connected()
    assert _client is not None
    try:
        out = OutputDevice(output)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    await _client.set_monitor_mix(serial, out)
    return {"ok": True, "output": output}


# ---------------------------------------------------------------------------
# EQ
# ---------------------------------------------------------------------------

@app.post("/api/mic/{serial}/eq/{freq}/gain/{gain}")
async def set_eq_gain(serial: str, freq: str, gain: int, mini: bool = False) -> dict[str, Any]:
    """Set EQ band gain (full or mini EQ)."""
    _require_connected()
    assert _client is not None
    if mini:
        try:
            mf = MiniEqFrequencies(freq)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        await _client.set_eq_mini_gain(serial, mf, gain)
    else:
        try:
            ef = EqFrequencies(freq)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        await _client.set_eq_gain(serial, ef, gain)
    return {"ok": True, "freq": freq, "gain": gain}


@app.post("/api/mic/{serial}/eq/{freq}/freq-value/{value}")
async def set_eq_freq(
    serial: str, freq: str, value: float, mini: bool = False
) -> dict[str, Any]:
    """Set EQ band center frequency (full or mini EQ)."""
    _require_connected()
    assert _client is not None
    if mini:
        try:
            mf = MiniEqFrequencies(freq)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        await _client.set_eq_mini_freq(serial, mf, value)
    else:
        try:
            ef = EqFrequencies(freq)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        await _client.set_eq_freq(serial, ef, value)
    return {"ok": True, "freq": freq, "value": value}


# ---------------------------------------------------------------------------
# Compressor / De-esser / Gate detail / Mic gain
# ---------------------------------------------------------------------------

@app.post("/api/mic/{serial}/compressor/threshold/{threshold}")
async def set_compressor_threshold(serial: str, threshold: int) -> dict[str, Any]:
    _require_connected()
    assert _client is not None
    await _client.set_compressor_threshold(serial, threshold)
    return {"ok": True, "threshold": threshold}


@app.post("/api/mic/{serial}/compressor/ratio/{ratio}")
async def set_compressor_ratio(serial: str, ratio: str) -> dict[str, Any]:
    _require_connected()
    assert _client is not None
    try:
        r = CompressorRatio(ratio)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    await _client.set_compressor_ratio(serial, r)
    return {"ok": True, "ratio": ratio}


@app.post("/api/mic/{serial}/compressor/attack/{attack}")
async def set_compressor_attack(serial: str, attack: str) -> dict[str, Any]:
    _require_connected()
    assert _client is not None
    try:
        a = CompressorAttackTime(attack)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    await _client.set_compressor_attack(serial, a)
    return {"ok": True, "attack": attack}


@app.post("/api/mic/{serial}/compressor/release/{release}")
async def set_compressor_release(serial: str, release: str) -> dict[str, Any]:
    _require_connected()
    assert _client is not None
    try:
        r = CompressorReleaseTime(release)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    await _client.set_compressor_release(serial, r)
    return {"ok": True, "release": release}


@app.post("/api/mic/{serial}/compressor/makeup/{gain}")
async def set_compressor_makeup_gain(serial: str, gain: int) -> dict[str, Any]:
    _require_connected()
    assert _client is not None
    await _client.set_compressor_makeup_gain(serial, gain)
    return {"ok": True, "gain": gain}


@app.post("/api/mic/{serial}/deeser/{amount}")
async def set_deeser(serial: str, amount: int) -> dict[str, Any]:
    """Set the de-esser amount (0–100)."""
    _require_connected()
    assert _client is not None
    await _client.set_deeser(serial, amount)
    return {"ok": True, "amount": amount}


@app.post("/api/mic/{serial}/gate/attenuation/{attenuation}")
async def set_gate_attenuation(serial: str, attenuation: int) -> dict[str, Any]:
    _require_connected()
    assert _client is not None
    await _client.set_gate_attenuation(serial, attenuation)
    return {"ok": True, "attenuation": attenuation}


@app.post("/api/mic/{serial}/gate/attack/{attack}")
async def set_gate_attack(serial: str, attack: str) -> dict[str, Any]:
    _require_connected()
    assert _client is not None
    try:
        a = GateTimes(attack)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    await _client.set_gate_attack(serial, a)
    return {"ok": True, "attack": attack}


@app.post("/api/mic/{serial}/gate/release/{release}")
async def set_gate_release(serial: str, release: str) -> dict[str, Any]:
    _require_connected()
    assert _client is not None
    try:
        r = GateTimes(release)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    await _client.set_gate_release(serial, r)
    return {"ok": True, "release": release}


@app.post("/api/mic/{serial}/gain/{mic_type}/{gain}")
async def set_microphone_gain(serial: str, mic_type: str, gain: int) -> dict[str, Any]:
    """Set microphone hardware gain (0–72 dB)."""
    _require_connected()
    assert _client is not None
    try:
        mt = MicrophoneType(mic_type)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    await _client.set_microphone_gain(serial, mt, gain)
    return {"ok": True, "mic_type": mic_type, "gain": gain}


# ---------------------------------------------------------------------------
# Scribble strips
# ---------------------------------------------------------------------------

@app.post("/api/scribble/{serial}/{fader}/text/{text}")
async def set_scribble_text(serial: str, fader: str, text: str) -> dict[str, Any]:
    _require_connected()
    assert _client is not None
    try:
        f = FaderName(fader)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    await _client.set_scribble_text(serial, f, text)
    return {"ok": True, "fader": fader, "text": text}


@app.post("/api/scribble/{serial}/{fader}/number/{number}")
async def set_scribble_number(serial: str, fader: str, number: str) -> dict[str, Any]:
    _require_connected()
    assert _client is not None
    try:
        f = FaderName(fader)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    await _client.set_scribble_number(serial, f, number)
    return {"ok": True, "fader": fader, "number": number}


@app.post("/api/scribble/{serial}/{fader}/invert/{invert}")
async def set_scribble_invert(serial: str, fader: str, invert: bool) -> dict[str, Any]:
    _require_connected()
    assert _client is not None
    try:
        f = FaderName(fader)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    await _client.set_scribble_invert(serial, f, invert)
    return {"ok": True, "fader": fader, "invert": invert}


# ---------------------------------------------------------------------------
# Megaphone detail
# ---------------------------------------------------------------------------

@app.post("/api/effects/{serial}/megaphone/style/{style}")
async def set_megaphone_style(serial: str, style: str) -> dict[str, Any]:
    _require_connected()
    assert _client is not None
    try:
        s = MegaphoneStyle(style)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    await _client.set_megaphone_style(serial, s)
    return {"ok": True, "style": style}


@app.post("/api/effects/{serial}/megaphone/amount/{amount}")
async def set_megaphone_amount(serial: str, amount: int) -> dict[str, Any]:
    _require_connected()
    assert _client is not None
    await _client.set_megaphone_amount(serial, amount)
    return {"ok": True, "amount": amount}


@app.post("/api/effects/{serial}/megaphone/post-gain/{gain}")
async def set_megaphone_post_gain(serial: str, gain: int) -> dict[str, Any]:
    _require_connected()
    assert _client is not None
    await _client.set_megaphone_post_gain(serial, gain)
    return {"ok": True, "gain": gain}


# ---------------------------------------------------------------------------
# Robot detail
# ---------------------------------------------------------------------------

@app.post("/api/effects/{serial}/robot/style/{style}")
async def set_robot_style(serial: str, style: str) -> dict[str, Any]:
    _require_connected()
    assert _client is not None
    try:
        s = RobotStyle(style)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    await _client.set_robot_style(serial, s)
    return {"ok": True, "style": style}


@app.post("/api/effects/{serial}/robot/{range_}/gain/{gain}")
async def set_robot_gain(serial: str, range_: str, gain: int) -> dict[str, Any]:
    _require_connected()
    assert _client is not None
    try:
        r = RobotRange(range_)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    await _client.set_robot_gain(serial, r, gain)
    return {"ok": True, "range": range_, "gain": gain}


@app.post("/api/effects/{serial}/robot/{range_}/freq/{freq}")
async def set_robot_freq(serial: str, range_: str, freq: int) -> dict[str, Any]:
    _require_connected()
    assert _client is not None
    try:
        r = RobotRange(range_)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    await _client.set_robot_freq(serial, r, freq)
    return {"ok": True, "range": range_, "freq": freq}


@app.post("/api/effects/{serial}/robot/{range_}/width/{width}")
async def set_robot_width(serial: str, range_: str, width: int) -> dict[str, Any]:
    _require_connected()
    assert _client is not None
    try:
        r = RobotRange(range_)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    await _client.set_robot_width(serial, r, width)
    return {"ok": True, "range": range_, "width": width}


# ---------------------------------------------------------------------------
# HardTune detail
# ---------------------------------------------------------------------------

@app.post("/api/effects/{serial}/hardtune/style/{style}")
async def set_hard_tune_style(serial: str, style: str) -> dict[str, Any]:
    _require_connected()
    assert _client is not None
    try:
        s = HardTuneStyle(style)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    await _client.set_hard_tune_style(serial, s)
    return {"ok": True, "style": style}


@app.post("/api/effects/{serial}/hardtune/amount/{amount}")
async def set_hard_tune_amount(serial: str, amount: int) -> dict[str, Any]:
    _require_connected()
    assert _client is not None
    await _client.set_hard_tune_amount(serial, amount)
    return {"ok": True, "amount": amount}


@app.post("/api/effects/{serial}/hardtune/rate/{rate}")
async def set_hard_tune_rate(serial: str, rate: int) -> dict[str, Any]:
    _require_connected()
    assert _client is not None
    await _client.set_hard_tune_rate(serial, rate)
    return {"ok": True, "rate": rate}


@app.post("/api/effects/{serial}/hardtune/source/{source}")
async def set_hard_tune_source(serial: str, source: str) -> dict[str, Any]:
    _require_connected()
    assert _client is not None
    try:
        s = HardTuneSource(source)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    await _client.set_hard_tune_source(serial, s)
    return {"ok": True, "source": source}


# ---------------------------------------------------------------------------
# Submix extras
# ---------------------------------------------------------------------------

@app.post("/api/submix/{serial}/linked/{channel}/{linked}")
async def set_submix_linked(serial: str, channel: str, linked: bool) -> dict[str, Any]:
    """Link a channel's submix B to its main volume."""
    _require_connected()
    assert _client is not None
    try:
        ch = ChannelName(channel)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    await _client.set_submix_linked(serial, ch, linked)
    return {"ok": True, "channel": channel, "linked": linked}


@app.post("/api/submix/{serial}/output-mix/{output}/{mix}")
async def set_submix_output_mix(serial: str, output: str, mix: str) -> dict[str, Any]:
    """Set which mix (A or B) is sent to an output."""
    _require_connected()
    assert _client is not None
    try:
        out = OutputDevice(output)
        m = Mix(mix)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    await _client.set_submix_output_mix(serial, out, m)
    return {"ok": True, "output": output, "mix": mix}


# ---------------------------------------------------------------------------
# Cough config
# ---------------------------------------------------------------------------

@app.post("/api/cough/{serial}/mute-function/{mute}")
async def set_cough_mute_function(serial: str, mute: str) -> dict[str, Any]:
    """Set the mute function for the cough button."""
    _require_connected()
    assert _client is not None
    try:
        mf = MuteFunction(mute)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    await _client.set_cough_mute_function(serial, mf)
    return {"ok": True, "mute": mute}


@app.post("/api/cough/{serial}/hold/{hold}")
async def set_cough_is_hold(serial: str, hold: bool) -> dict[str, Any]:
    """Set whether cough button acts as hold (True) or toggle (False)."""
    _require_connected()
    assert _client is not None
    await _client.set_cough_is_hold(serial, hold)
    return {"ok": True, "hold": hold}


# ---------------------------------------------------------------------------
# Misc
# ---------------------------------------------------------------------------

@app.post("/api/misc/{serial}/lock-faders/{locked}")
async def set_lock_faders(serial: str, locked: bool) -> dict[str, Any]:
    """Lock or unlock all faders."""
    _require_connected()
    assert _client is not None
    await _client.set_lock_faders(serial, locked)
    return {"ok": True, "locked": locked}
