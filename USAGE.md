# goxlrutil_api – Usage Guide

A comprehensive reference for humans and AI agents integrating with the library.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Transports](#transports)
4. [Quick Start](#quick-start)
5. [GoXLRClient API](#goxlrclient-api)
6. [Sending Commands](#sending-commands)
7. [Reading State](#reading-state)
8. [Live Updates via Patches](#live-updates-via-patches)
9. [Button Events](#button-events)
10. [Lighting & Colours](#lighting--colours)
11. [Effects & Sampler](#effects--sampler)
12. [Error Handling](#error-handling)
13. [Synchronous Wrapper](#synchronous-wrapper)
14. [Full Integration Example](#full-integration-example)
15. [Protocol Notes](#protocol-notes)

---

## Prerequisites

- **goxlr-utility daemon** must be running locally.
  - Repository: https://github.com/GoXLR-on-Linux/goxlr-utility
  - The daemon exposes:
    - Unix socket: `/tmp/goxlr.socket` (request/response only, no live events)
    - HTTP API: `http://localhost:14564/api/command` (request/response only)
    - WebSocket: `ws://localhost:14564/api/websocket` (**required** for live patch events and button presses)

---

## Installation

```bash
pip install goxlrutil-api
```

Or with Poetry:

```bash
poetry add goxlrutil-api
```

---

## Transports

Three transports are available. Choose based on your use case:

| Transport | Import | Live Events | Use When |
|---|---|---|---|
| `WebSocketTransport` | `from goxlrutil_api import WebSocketTransport` | ✅ Yes | **Recommended default.** Required for button events, volume changes, and any live state updates. |
| `UnixSocketTransport` | `from goxlrutil_api import UnixSocketTransport` | ❌ No | Simple scripts that only send commands or read state once. |
| `HttpTransport` | `from goxlrutil_api import HttpTransport` | ❌ No | Remote access or environments without Unix socket access. |

> **Important:** Live patch events (button presses, fader moves, etc.) are only pushed by the
> daemon over the **WebSocket** connection. The Unix socket and HTTP transports are
> strictly request/response — they will never receive unsolicited events.

```python
from goxlrutil_api import WebSocketTransport, UnixSocketTransport, HttpTransport

# WebSocket – full-featured, recommended
transport = WebSocketTransport("ws://localhost:14564/api/websocket")

# Unix socket – request/response only
transport = UnixSocketTransport()  # defaults to /tmp/goxlr.socket

# HTTP – request/response only, works remotely
transport = HttpTransport("http://localhost:14564")
```

---

## Quick Start

```python
import asyncio
from goxlrutil_api import GoXLRClient, WebSocketTransport
from goxlrutil_api.protocol.types import ChannelName

async def main():
    transport = WebSocketTransport()
    async with GoXLRClient(transport) as client:
        status = await client.get_status()
        serial = next(iter(status.mixers))
        mixer = status.mixers[serial]

        print(f"Device: {mixer.hardware.device_type.value}")
        print(f"Profile: {mixer.profile_name}")
        print(f"Mic volume: {mixer.levels.volumes.get('Mic', 0)}")

        # Set microphone volume to 200 (out of 255)
        await client.set_volume(serial, ChannelName.Mic, 200)

asyncio.run(main())
```

---

## GoXLRClient API

```python
GoXLRClient(
    transport: Transport,
    on_state_update: PatchListener | None = None,  # called after every patch
    on_button_event: ButtonListener | None = None,  # called on press/release/long-press
    long_press_threshold: float = 0.5,             # seconds before long_pressed fires
)
```

The client is an **async context manager**. Always use it with `async with`:

```python
async with GoXLRClient(transport) as client:
    ...
# Connection is cleanly closed after the block, including cancelling any
# pending long-press timers.
```

### Methods

| Method | Returns | Description |
|---|---|---|
| `await client.ping()` | `bool` | Returns `True` if daemon responds. |
| `await client.get_status()` | `DaemonStatus` | Fetches full state and updates internal cache. |
| `await client.get_mic_level(serial)` | `float` | Current mic level (0.0–1.0). |
| `await client.command(serial, cmd)` | `None` | Send any `GoXLRCommand`. |
| `await client.set_volume(serial, channel, volume)` | `None` | Set channel volume (0–255). |
| `await client.set_fader_mute_state(serial, fader, state)` | `None` | Mute/unmute a fader. |
| `await client.set_fx_enabled(serial, enabled)` | `None` | Enable or disable effects. |
| `client.state` | `DaemonState` | Access the live internal state cache. |

---

## Sending Commands

### Volume

```python
from goxlrutil_api.protocol.types import ChannelName

# ChannelName values:
# Mic, LineIn, Console, System, Game, Chat, Sample, Music,
# Headphones, MicMonitor, LineOut

await client.set_volume(serial, ChannelName.Mic, 200)       # 0–255
await client.set_volume(serial, ChannelName.Game, 128)
await client.set_volume(serial, ChannelName.Headphones, 255)
```

### Fader Mute

```python
from goxlrutil_api.protocol.types import FaderName, MuteState

# FaderName values: A, B, C, D
# MuteState values: Unmuted, MutedToAll, MutedToX

await client.set_fader_mute_state(serial, FaderName.A, MuteState.MutedToAll)
await client.set_fader_mute_state(serial, FaderName.A, MuteState.Unmuted)
```

### Effects (FX)

```python
from goxlrutil_api.protocol.types import EffectBankPresets

# Global FX on/off
await client.set_fx_enabled(serial, True)
await client.set_fx_enabled(serial, False)

# Toggle (reads current state from cache, returns new bool)
is_on = await client.toggle_fx(serial)

# Switch active effect preset (Preset1 – Preset6)
await client.set_active_effect_preset(serial, EffectBankPresets.Preset1)

# Megaphone
await client.set_megaphone_enabled(serial, True)
enabled = await client.toggle_megaphone(serial)   # returns new bool

# Robot voice
await client.set_robot_enabled(serial, True)
enabled = await client.toggle_robot(serial)

# Hard Tune
await client.set_hard_tune_enabled(serial, True)
enabled = await client.toggle_hard_tune(serial)
```

`EffectBankPresets` values: `Preset1`, `Preset2`, `Preset3`, `Preset4`, `Preset5`, `Preset6`

> **Note:** Toggle methods read from the in-memory state cache.
> Call `await client.get_status()` at least once (or connect via WebSocket) before using them.

### Sampler

```python
from goxlrutil_api.protocol.types import SampleBank, SampleButtons

# Trigger playback of a sample in a specific bank + button slot
await client.play_sample(serial, SampleBank.A, SampleButtons.TopLeft)

# Stop playback for a slot
await client.stop_sample(serial, SampleBank.A, SampleButtons.TopLeft)
```

`SampleBank` values: `A`, `B`, `C`

`SampleButtons` values: `TopLeft`, `TopRight`, `BottomLeft`, `BottomRight`

Example — play all four slots in bank B then stop them:

```python
for button in SampleButtons:
    await client.play_sample(serial, SampleBank.B, button)

# … later …

for button in SampleButtons:
    await client.stop_sample(serial, SampleBank.B, button)
```

### Raw Commands

Use `GoXLRCommand` directly for commands not covered by convenience helpers:

```python
from goxlrutil_api.protocol.commands import GoXLRCommand
from goxlrutil_api.protocol.types import FaderName, ChannelName, MuteFunction

# Assign a channel to a fader
await client.command(serial, GoXLRCommand.set_fader(FaderName.A, ChannelName.Mic))

# Set mute function for a fader
await client.command(serial, GoXLRCommand.set_fader_mute_function(FaderName.A, MuteFunction.All))
```

---

## Reading State

After `await client.get_status()`, the state is cached in `client.state`. Subsequent patch
events (over WebSocket) update the cache automatically.

```python
status = await client.get_status()

# Iterate all connected mixers
for serial, mixer in status.mixers.items():
    print(f"Serial: {serial}")
    print(f"Device type: {mixer.hardware.device_type.value}")  # "Full" or "Mini"
    print(f"Profile: {mixer.profile_name}")
    print(f"Mic profile: {mixer.mic_profile_name}")

    # Volumes (channel name → int 0–255)
    for channel, vol in mixer.levels.volumes.items():
        print(f"  {channel}: {vol}")

    # Fader assignments and mute state
    for fname, fs in mixer.fader_status.items():
        print(f"  Fader {fname}: {fs.channel.value} – {fs.mute_state.value}")

    # Button state (button name → bool, True = currently held down)
    for btn, is_down in mixer.button_down.items():
        if is_down:
            print(f"  {btn} is held")

    # Effects
    if mixer.effects:
        print(f"  FX enabled: {mixer.effects.is_enabled}")
```

### Accessing Cached State

```python
# After connecting, the cache updates on every WebSocket patch.
# Read it at any time without an async call:
mixer = client.state.status.mixers.get(serial)
if mixer:
    mic_vol = mixer.levels.volumes.get("Mic", 0)
```

---

## Live Updates via Patches

The daemon pushes [RFC 6902 JSON Patch](https://jsonpatch.com/) operations over WebSocket
whenever state changes. The library applies these patches to the internal cache automatically.

Register an `on_state_update` callback to be notified after each patch:

```python
from goxlrutil_api import GoXLRClient, WebSocketTransport, PatchListener
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
from goxlrutil_api import GoXLRClient, WebSocketTransport, ButtonListener
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
            print("Bleep button pressed – activating sound effect")
        elif event.event_type == ButtonEventType.long_pressed:
            print("Bleep held – activating extended effect")
```

---

## Lighting & Colours

The library exposes the full GoXLR LED control API.  Colours are passed as
either a `Colour` instance or a plain 6-character hex string (`RRGGBB` without
`#`).

### The `Colour` helper

```python
from goxlrutil_api import Colour

# From RGB components
red   = Colour(255, 0, 0)
teal  = Colour(0, 200, 180)

# From hex strings (# is optional)
orange = Colour.from_hex("#FF8800")
white  = Colour.from_hex("FFFFFF")

# From a packed 24-bit integer
blue = Colour.from_int(0x0000FF)

# Named constants
Colour.BLACK    # (0, 0, 0)
Colour.WHITE    # (255, 255, 255)
Colour.RED      # (255, 0, 0)
Colour.GREEN    # (0, 255, 0)
Colour.BLUE     # (0, 0, 255)
Colour.YELLOW   # (255, 255, 0)
Colour.CYAN     # (0, 255, 255)
Colour.MAGENTA  # (255, 0, 255)
Colour.ORANGE   # (255, 128, 0)
Colour.PURPLE   # (128, 0, 255)
Colour.PINK     # (255, 105, 180)

# Dim a colour to e.g. 30 % brightness (default factor)
dimmed_red = Colour.RED.dimmed()          # Colour(76, 0, 0)
dimmed_red = Colour.RED.dimmed(0.1)       # Colour(25, 0, 0)

# str(colour) → "FF0000" — the daemon wire format
print(str(Colour.RED))   # → "FF0000"
```

Plain hex strings are accepted wherever a `Colour` is expected:

```python
await client.set_global_colour(serial, "FF8800")  # orange, no Colour object needed
```

### Global & simple colour targets

```python
from goxlrutil_api.protocol.types import SimpleColourTargets

# Global accent colour (affects animations and unassigned LEDs)
await client.set_global_colour(serial, Colour.PURPLE)

# Named single-colour targets: Global, Accent, ScribbleBack
await client.set_simple_colour(serial, SimpleColourTargets.Accent, Colour.CYAN)
await client.set_simple_colour(serial, SimpleColourTargets.ScribbleBack, "#1A1A2E")
```

### Button colours

Each button has an *on* (active) colour and an *off* (inactive) colour.

```python
from goxlrutil_api.protocol.types import Button

# Set active colour; off colour defaults to a 30 % dimmed version of on colour
await client.set_button_colour(serial, Button.Bleep, Colour.RED)

# Set both explicitly
await client.set_button_colour(serial, Button.Cough, Colour.ORANGE, Colour.from_hex("331100"))

# All Button values:
# Fader1Mute, Fader2Mute, Fader3Mute, Fader4Mute
# Bleep, Cough
# EffectSelect1 … EffectSelect6
# EffectFx, EffectMegaphone, EffectRobot, EffectHardTune
# SamplerSelectA, SamplerSelectB, SamplerSelectC
# SamplerTopLeft, SamplerTopRight, SamplerBottomLeft, SamplerBottomRight, SamplerClear
```

#### Button off-state style

Control how a button looks when it is inactive:

```python
from goxlrutil_api.protocol.types import Button, ButtonColourOffStyle

# ButtonColourOffStyle values: Dimmed, Colour2, Dimmed2
await client.set_button_off_style(serial, Button.Bleep, ButtonColourOffStyle.Dimmed)
await client.set_button_off_style(serial, Button.Cough, ButtonColourOffStyle.Colour2, Colour.BLUE)
```

#### Button group colours

Set colours for all buttons in a logical group at once:

```python
from goxlrutil_api.protocol.types import ButtonColourGroups

# ButtonColourGroups values: FaderMute, EffectSelector, EffectTypes
await client.set_button_group_colour(serial, ButtonColourGroups.FaderMute, Colour.BLUE, Colour.from_hex("001040"))
await client.set_button_group_colour(serial, ButtonColourGroups.EffectTypes, Colour.GREEN, Colour.from_hex("003300"))
```

### Fader colours

Each fader strip has a top and a bottom colour (the gradient between them is
controlled by the *display style*):

```python
from goxlrutil_api.protocol.types import FaderName, FaderDisplayStyle

# Set top and bottom colours for fader A
await client.set_fader_colour(serial, FaderName.A, Colour.CYAN, Colour.BLUE)
await client.set_fader_colour(serial, FaderName.B, "#00FF88", "#0044FF")

# Set display style for a single fader
# FaderDisplayStyle values: TwoColour, Gradient, Meter, GradientMeter
await client.set_fader_display_style(serial, FaderName.A, FaderDisplayStyle.Gradient)

# Apply one style to all four faders simultaneously
await client.set_all_fader_display_style(serial, FaderDisplayStyle.GradientMeter)
```

### Encoder colours

Each effect encoder (Reverb, Pitch, Echo, Gender) has three LED zones:

```python
from goxlrutil_api.protocol.types import EncoderColourTargets

# EncoderColourTargets values: Reverb, Pitch, Echo, Gender
await client.set_encoder_colour(
    serial,
    EncoderColourTargets.Reverb,
    colour_left=Colour.BLUE,    # left arc
    colour_right=Colour.CYAN,   # right arc
    colour_knob=Colour.WHITE,   # knob LED
)
```

### Sampler colours

Each sampler bank-select button (A, B, C) has three LED states:

```python
from goxlrutil_api.protocol.types import SamplerColourTargets, ButtonColourOffStyle

# SamplerColourTargets values: SamplerSelectA, SamplerSelectB, SamplerSelectC
await client.set_sampler_colour(
    serial,
    SamplerColourTargets.SamplerSelectA,
    colour_one=Colour.GREEN,
    colour_two=Colour.from_hex("003300"),
    colour_three=Colour.YELLOW,
)

# Off-state style for a sampler selector button
await client.set_sampler_off_style(
    serial,
    SamplerColourTargets.SamplerSelectA,
    ButtonColourOffStyle.Dimmed,
)
```

### Animation mode

```python
from goxlrutil_api.protocol.types import AnimationMode, WaterfallDirection

# AnimationMode values:
#   RetroRainbow, RainbowDark, RainbowBright, Simple, Ripple, None_

# Animated rainbow across all LEDs
await client.set_animation_mode(serial, AnimationMode.RainbowBright)

# Simple static animation with custom colours and waterfall direction
# WaterfallDirection values: Down, Up, Off
await client.set_animation_mode(
    serial,
    AnimationMode.Simple,
    colour_one=Colour.BLUE,
    colour_two=Colour.CYAN,
    waterfall=WaterfallDirection.Down,
)

# Disable animation
await client.set_animation_mode(serial, AnimationMode.None_)
```

### Raw lighting commands

All lighting methods map to `GoXLRCommand` factory methods for use with `client.command()`:

```python
from goxlrutil_api.protocol.commands import GoXLRCommand
from goxlrutil_api.protocol.types import Button, FaderName, SimpleColourTargets

# Equivalent raw calls (colours as RRGGBB hex strings):
await client.command(serial, GoXLRCommand.set_button_colours(Button.Bleep, "FF0000", "330000"))
await client.command(serial, GoXLRCommand.set_fader_colours(FaderName.A, "00FF88", "0044FF"))
await client.command(serial, GoXLRCommand.set_global_colour("FF8800"))
await client.command(serial, GoXLRCommand.set_simple_colour(SimpleColourTargets.Accent, "AA00FF"))
```

---

## Effects & Sampler

See [Sending Commands → Effects (FX)](#effects-fx) and [Sending Commands → Sampler](#sampler) for the full reference.

Quick summary:

```python
from goxlrutil_api.protocol.types import EffectBankPresets, SampleBank, SampleButtons

# --- Effects ---
await client.set_fx_enabled(serial, True)
await client.toggle_fx(serial)                                         # → bool
await client.set_active_effect_preset(serial, EffectBankPresets.Preset3)
await client.toggle_megaphone(serial)                                  # → bool
await client.toggle_robot(serial)                                      # → bool
await client.toggle_hard_tune(serial)                                  # → bool

# --- Sampler ---
await client.play_sample(serial, SampleBank.A, SampleButtons.TopLeft)
await client.stop_sample(serial, SampleBank.A, SampleButtons.TopLeft)
```

---

## Error Handling

```python
from goxlrutil_api.exceptions import GoXLRError, ConnectionError, CommandError, ProtocolError

try:
    async with GoXLRClient(transport) as client:
        await client.set_volume(serial, ChannelName.Mic, 200)

except ConnectionError as e:
    # Daemon not running or socket/WebSocket unavailable
    print(f"Cannot connect: {e}")

except CommandError as e:
    # Daemon returned an error response (e.g. unknown serial, invalid value)
    print(f"Command rejected: {e}")

except ProtocolError as e:
    # Unexpected data from daemon (framing or JSON issue)
    print(f"Protocol error: {e}")

except GoXLRError as e:
    # Base class for all library exceptions
    print(f"GoXLR error: {e}")
```

---

## Synchronous Wrapper

For scripts that do not use `asyncio`, a thin synchronous wrapper is available.
It does **not** support callbacks (`on_state_update`, `on_button_event`).

```python
from goxlrutil_api.sync import GoXLRClientSync
from goxlrutil_api import UnixSocketTransport
from goxlrutil_api.protocol.types import ChannelName

transport = UnixSocketTransport()
with GoXLRClientSync(transport) as client:
    status = client.get_status()
    serial = next(iter(status.mixers))
    client.set_volume(serial, ChannelName.Mic, 200)
    print("Done")
```

---

## Full Integration Example

A complete example combining state reading, live updates, and button events:

```python
import asyncio
from goxlrutil_api import GoXLRClient, WebSocketTransport
from goxlrutil_api.events import ButtonEvent, ButtonEventType
from goxlrutil_api.protocol.responses import DaemonStatus
from goxlrutil_api.protocol.types import Button, ChannelName, MuteState, FaderName
from goxlrutil_api.exceptions import GoXLRError


async def on_state_update(status: DaemonStatus) -> None:
    """Called after every patch event from the daemon."""
    for serial, mixer in status.mixers.items():
        mic = mixer.levels.volumes.get("Mic", 0)
        # Example: react to mic volume dropping to 0
        if mic == 0:
            print(f"[{serial}] Warning: Mic volume is 0")


async def on_button_event(event: ButtonEvent) -> None:
    """Called on every button press, release, or long-press."""
    serial = event.serial

    if event.button_enum == Button.Bleep and event.event_type == ButtonEventType.pressed:
        print(f"[{serial}] Bleep activated")

    if event.button_enum == Button.Cough:
        if event.event_type == ButtonEventType.pressed:
            print(f"[{serial}] Cough mute: ON")
        elif event.event_type == ButtonEventType.released:
            print(f"[{serial}] Cough mute: OFF (held {event.held_seconds:.2f}s)")

    # Long-press Fader1Mute to mute all
    if (
        event.button_enum == Button.Fader1Mute
        and event.event_type == ButtonEventType.long_pressed
    ):
        print(f"[{serial}] Long-press detected – would mute all faders here")


async def main() -> None:
    transport = WebSocketTransport("ws://localhost:14564/api/websocket")

    try:
        async with GoXLRClient(
            transport,
            on_state_update=on_state_update,
            on_button_event=on_button_event,
            long_press_threshold=0.8,
        ) as client:
            # Fetch and cache initial state
            status = await client.get_status()
            serial = next(iter(status.mixers))
            mixer = status.mixers[serial]

            print(f"Connected: {mixer.hardware.device_type.value} [{serial}]")
            print(f"Profile: {mixer.profile_name}")

            # Send an initial command
            await client.set_volume(serial, ChannelName.Headphones, 220)

            # Keep running and receive live events
            print("Listening for events. Press Ctrl+C to stop.")
            await asyncio.Event().wait()  # run forever

    except GoXLRError as e:
        print(f"GoXLR error: {e}")
    except KeyboardInterrupt:
        print("Stopped.")


if __name__ == "__main__":
    asyncio.run(main())
```

---

## Protocol Notes

These details are useful when extending the library or debugging.

### Wire Format

| Transport | Format |
|---|---|
| Unix socket | 4-byte big-endian `uint32` length prefix + UTF-8 JSON payload. Request: raw `DaemonRequest`. Response: raw `DaemonResponse`. |
| HTTP | `POST /api/command` with JSON body `<DaemonRequest>`, returns JSON `<DaemonResponse>`. |
| WebSocket | Messages are `{"id": <uint64>, "data": <DaemonRequest/DaemonResponse>}`. Unsolicited patch events arrive as `{"id": 0, "data": {"Patch": [<ops>]}}`. |

### DaemonRequest Variants

```
"Ping"
"GetStatus"
{"GetMicLevel": "<serial>"}
{"Command": ["<serial>", <GoXLRCommand>]}
{"Daemon": <DaemonCommand>}
```

### DaemonResponse Variants

```
"Ok"
{"Error": "<message>"}
{"Status": <DaemonStatus>}
{"Patch": [<RFC 6902 operations>]}
{"MicLevel": <float>}
```

### JSON Patch Paths

Patch operations use paths rooted at the `Status` object, for example:

```json
{"op": "replace", "path": "/mixers/S210400463CQK/button_down/Bleep", "value": true}
{"op": "replace", "path": "/mixers/S210400463CQK/levels/volumes/Mic", "value": 200}
{"op": "replace", "path": "/mixers/S210400463CQK/fader_status/A/mute_state", "value": "MutedToAll"}
```

### Important Constraints

- Button events **require** WebSocket transport — the Unix socket and HTTP transports never receive patches.
- `long_pressed` fires while the button is still held; a `released` event will follow when the button is let go.
- The serial number changes per physical device. Always discover it via `get_status()` — never hardcode it.
- `button_down` only reflects currently-held hardware buttons. Software mute state is tracked separately in `fader_status[fader].mute_state`.
