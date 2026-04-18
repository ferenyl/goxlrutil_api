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
    EffectBankPresets,
    FaderName,
    MuteState,
    SampleBank,
    SampleButtons,
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
