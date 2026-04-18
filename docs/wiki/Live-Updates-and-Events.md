# Live Updates & Events

Live updates require **WebSocket transport** (`WebSocketTransport`).

---

## Live Updates via Patches

The daemon pushes [RFC 6902 JSON Patch](https://jsonpatch.com/) operations over WebSocket
whenever state changes. The library applies these patches to the internal cache automatically.

Register an `on_state_update` callback to be notified after each patch:

```python
from goxlrutil_api import GoXLRClient, WebSocketTransport
from goxlrutil_api.protocol.responses import DaemonStatus

async def on_update(status: DaemonStatus) -> None:
    for serial, mixer in status.mixers.items():
        mic = mixer.levels.volumes.get("Mic", 0)
        print(f"[{serial}] Mic volume: {mic}")

transport = WebSocketTransport()
async with GoXLRClient(transport, on_state_update=on_update) as client:
    await client.get_status()          # populate initial state
    await asyncio.sleep(60)            # listen for 60 seconds
```

> `on_state_update` is called after **every** patch, including minor changes. Debounce or
> filter inside the callback if needed.

---

## Reconnection & Connection Events

`WebSocketTransport` reconnects automatically when the daemon restarts or the
connection drops. Reconnection is enabled by default and uses exponential backoff.

```python
transport = WebSocketTransport(
    reconnect=True,           # default – disable with False
    reconnect_delay=1.0,      # initial wait in seconds
    max_reconnect_delay=60.0, # upper bound on wait
)
```

Supply `on_connect` and `on_disconnect` callbacks to `GoXLRClient` to be
notified when the connection state changes. On reconnect the client
automatically re-fetches the full daemon status so the state cache is
immediately up to date before `on_connect` is called.

```python
async def on_connect() -> None:
    print("Connected – mixer is available")

async def on_disconnect() -> None:
    print("Disconnected – mixer is unavailable")

async with GoXLRClient(
    transport,
    on_connect=on_connect,
    on_disconnect=on_disconnect,
) as client:
    await client.get_status()
    await asyncio.sleep(3600)
```

---

## Button Events

Button events require **WebSocket transport**. The daemon pushes a patch whenever a button's
state changes in `button_down`.

### Event Types

| `ButtonEventType` | Fires when |
|---|---|
| `pressed` | Button transitions from not-held to held. `held_seconds` is always `0.0`. |
| `released` | Button transitions from held to not-held. `held_seconds` is total hold duration. |
| `long_pressed` | Button has been held for `long_press_threshold` seconds (default 0.5s). |

### ButtonEvent Fields

```python
@dataclass
class ButtonEvent:
    serial: str               # mixer serial number
    button: str               # button name as string, e.g. "Bleep"
    event_type: ButtonEventType
    button_enum: Button | None  # typed enum, None for unknown buttons
    held_seconds: float        # seconds held (0.0 for pressed events)
```

### All Button Names

```python
from goxlrutil_api.protocol.types import Button

# Fader mute buttons
Button.Fader1Mute, Button.Fader2Mute, Button.Fader3Mute, Button.Fader4Mute

# Special buttons
Button.Bleep        # swear/bleep button
Button.Cough        # cough/mute button

# Effect preset buttons
Button.EffectSelect1 … Button.EffectSelect6
Button.EffectFx
Button.EffectMegaphone
Button.EffectRobot
Button.EffectHardTune

# Sampler bank buttons
Button.SamplerSelectA, Button.SamplerSelectB, Button.SamplerSelectC

# Sampler trigger buttons
Button.SamplerTopLeft, Button.SamplerTopRight
Button.SamplerBottomLeft, Button.SamplerBottomRight
Button.SamplerClear
```

### Usage

```python
import asyncio
from goxlrutil_api import GoXLRClient, WebSocketTransport
from goxlrutil_api.events import ButtonEvent, ButtonEventType

async def on_button(event: ButtonEvent) -> None:
    if event.event_type == ButtonEventType.pressed:
        print(f"[{event.serial}] {event.button} pressed")

    elif event.event_type == ButtonEventType.released:
        print(f"[{event.serial}] {event.button} released after {event.held_seconds:.2f}s")

    elif event.event_type == ButtonEventType.long_pressed:
        print(f"[{event.serial}] {event.button} LONG PRESS ({event.held_seconds:.2f}s)")

transport = WebSocketTransport()
async with GoXLRClient(
    transport,
    on_button_event=on_button,
    long_press_threshold=0.5,   # seconds, default 0.5
) as client:
    await client.get_status()
    await asyncio.sleep(60)
```

### Filtering by Button

```python
from goxlrutil_api.protocol.types import Button

async def on_button(event: ButtonEvent) -> None:
    if event.button_enum == Button.Bleep:
        if event.event_type == ButtonEventType.pressed:
            print("Bleep button pressed")
        elif event.event_type == ButtonEventType.long_pressed:
            print("Bleep held – long press")
```
