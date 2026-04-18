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
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, suppress
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from goxlrutil_api import GoXLRClient, UnixSocketTransport, WebSocketTransport
from goxlrutil_api.exceptions import GoXLRError
from goxlrutil_api.protocol.commands import GoXLRCommand
from goxlrutil_api.protocol.responses import DaemonStatus
from goxlrutil_api.protocol.types import ChannelName, FaderName, MuteState

_log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Transport selection: prefer WebSocket for live updates, fall back to socket
# ---------------------------------------------------------------------------
_USE_WS = os.getenv("GOXLR_USE_WS", "0") == "1"
_WS_URL = os.getenv("GOXLR_WS_URL", "ws://localhost:14564/api/websocket")

_client: GoXLRClient | None = None
_status: DaemonStatus | None = None
_connected = False


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:  # type: ignore[type-arg]
    global _client, _status, _connected
    transport = WebSocketTransport(_WS_URL) if _USE_WS else UnixSocketTransport()
    _client = GoXLRClient(transport)
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

_BASE = __file__[: __file__.rfind("/")]
templates = Jinja2Templates(directory=f"{_BASE}/templates")
app.mount("/static", StaticFiles(directory=f"{_BASE}/static"), name="static")


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


@app.post("/api/mute/{serial}/{fader}/{state}")
async def set_mute(serial: str, fader: str, state: str) -> dict[str, Any]:
    _require_connected()
    try:
        f = FaderName(fader)
        s = MuteState(state)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    assert _client is not None
    await _client.command(serial, GoXLRCommand.set_fader_mute_state(f, s))
    return {"ok": True, "fader": fader, "state": state}


@app.post("/api/fx/{serial}/{enabled}")
async def set_fx(serial: str, enabled: str) -> dict[str, Any]:
    _require_connected()
    assert _client is not None
    await _client.command(serial, GoXLRCommand.set_fx_enabled(enabled.lower() == "true"))
    return {"ok": True, "fx_enabled": enabled}


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


def _require_connected() -> None:
    if not _connected or _client is None:
        raise HTTPException(status_code=503, detail="Not connected to GoXLR daemon")
