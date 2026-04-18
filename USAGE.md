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
9. [Reconnection & Connection Events](#reconnection--connection-events)
10. [Button Events](#button-events)
11. [Lighting & Colours](#lighting--colours)
12. [Effects & Sampler](#effects--sampler)
13. [Fader Assignment & Routing](#fader-assignment--routing)
14. [Effect Parameters](#effect-parameters)
15. [Mic Settings](#mic-settings)
16. [EQ](#eq)
17. [Compressor](#compressor)
18. [De-esser](#de-esser)
19. [Scribble Strips](#scribble-strips)
20. [Mix, Monitor & Submix](#mix-monitor--submix)
21. [Cough Button](#cough-button)
22. [Profiles](#profiles)
23. [Sampler Management](#sampler-management)
24. [Misc Settings](#misc-settings)
25. [Error Handling](#error-handling)
26. [Synchronous Wrapper](#synchronous-wrapper)
27. [Full Integration Example](#full-integration-example)
28. [Protocol Notes](#protocol-notes)
29. [Logging](#logging)
30. [Importing Callback and State Types](#importing-callback-and-state-types)

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
    on_state_update: PatchListener | None = None,    # called after every patch
    on_button_event: ButtonListener | None = None,   # called on press/release/long-press
    on_connect: ConnectListener | None = None,       # called when connection is established / restored
    on_disconnect: DisconnectListener | None = None, # called when connection is lost
    long_press_threshold: float = 0.5,               # seconds before long_pressed fires
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
| `await client.set_volume_pct(serial, channel, pct)` | `None` | Set channel volume as percentage (0–100). |
| `await client.set_fader_mute_state(serial, fader, state)` | `None` | Mute/unmute a fader. |
| `await client.set_fx_enabled(serial, enabled)` | `None` | Enable or disable effects. |
| `client.get_mixer(serial)` | `MixerStatus \| None` | Cached mixer state — no network call. |
| `client.serials` | `list[str]` | Serial numbers of all connected mixers (from cache). Requires at least one `get_status()` call to be populated. |
| `client.state` | `DaemonState` | Access the live internal state cache. |

---

## Sending Commands

### Profiles

```python
# List all available profiles
profiles = await client.list_profiles(serial)
print(profiles)  # ['Default', 'Streaming', 'Gaming', ...]

# Get the currently loaded profile name
current = await client.get_current_profile(serial)
print(current)  # 'Streaming'

# Load a profile (saves to daemon config by default)
await client.load_profile(serial, "Gaming")

# Mic profiles work the same way
mic_profiles = await client.list_mic_profiles(serial)
current_mic = await client.get_current_mic_profile(serial)
await client.load_mic_profile(serial, "StudioMic")
```

### Volume

```python
from goxlrutil_api.protocol.types import ChannelName

# ChannelName values:
# Mic, LineIn, Console, System, Game, Chat, Sample, Music,
# Headphones, MicMonitor, LineOut

await client.set_volume(serial, ChannelName.Mic, 200)       # 0–255
await client.set_volume(serial, ChannelName.Game, 128)
await client.set_volume(serial, ChannelName.Headphones, 255)

# Percentage variant – maps 0–100 % to 0–255, clamped and rounded
await client.set_volume_pct(serial, ChannelName.Mic, 75.0)  # ≈ 191/255
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

### Reacting to connect / disconnect

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

### Reading cached state without a network call

`get_mixer(serial)` returns the cached `MixerStatus` synchronously. Use this
in callbacks and tight loops where you already have fresh state and do not want
an extra round-trip:

```python
async def on_update(status: DaemonStatus) -> None:
    mixer = client.get_mixer(serial)   # zero-latency, no network call
    if mixer:
        vol = mixer.levels.volumes.get("Mic", 0)
        print(f"Mic: {vol}/255")
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

## Fader Assignment & Routing

### Assigning channels to faders

```python
from goxlrutil_api.protocol.types import FaderName, ChannelName, MuteFunction, MuteState

# Assign the Mic channel to fader A
await client.set_fader(serial, FaderName.A, ChannelName.Mic)

# Change how the fader A mute button behaves
# MuteFunction: All, ToStream, ToVoiceChat, ToPhones, ToLineOut
await client.set_fader_mute_function(serial, FaderName.A, MuteFunction.All)

# Set the cough button mute state
await client.set_cough_mute_state(serial, MuteState.MutedToAll)
```

### Routing matrix

The routing matrix controls which input signals are routed to which output buses.

```python
from goxlrutil_api.protocol.types import InputDevice, OutputDevice

# Enable Mic → BroadcastMix cross-point
await client.set_router(serial, InputDevice.Microphone, OutputDevice.BroadcastMix, True)

# Disable Chat → Headphones cross-point
await client.set_router(serial, InputDevice.Chat, OutputDevice.Headphones, False)
```

**InputDevice values:** `Microphone`, `Chat`, `Music`, `Game`, `Console`, `LineIn`, `System`, `Samples`

**OutputDevice values:** `Headphones`, `BroadcastMix`, `LineOut`, `ChatMic`, `Sampler`

---

## Effect Parameters

Fine-tune the reverb, echo, pitch, and gender shift effects on the active preset.

```python
from goxlrutil_api.protocol.types import ReverbStyle, EchoStyle, PitchStyle, GenderStyle

# Reverb style and amount (0–100)
await client.set_reverb_style(serial, ReverbStyle.HockeyArena)
await client.set_reverb_amount(serial, 40)

# Echo style and amount (0–100)
await client.set_echo_style(serial, EchoStyle.Studio)
await client.set_echo_amount(serial, 25)

# Pitch shift style and amount
# Without HardTune: -24–24 (Wide) or same range applies for Narrow
# With HardTune enabled: -2–2 (Wide) or -1–1 (Narrow)
await client.set_pitch_style(serial, PitchStyle.Wide)
await client.set_pitch_amount(serial, -12)

# Gender shift style and amount
# Narrow style: -12–12  |  Wide style: -50–50
await client.set_gender_style(serial, GenderStyle.Medium)
await client.set_gender_amount(serial, 6)
```

### Reverb fine parameters

```python
await client.set_reverb_decay(serial, 800)         # ms
await client.set_reverb_early_level(serial, -6)    # dB
await client.set_reverb_tail_level(serial, -10)    # dB
await client.set_reverb_pre_delay(serial, 20)      # ms
await client.set_reverb_low_colour(serial, 50)
await client.set_reverb_high_colour(serial, 50)
await client.set_reverb_high_factor(serial, 50)
await client.set_reverb_diffuse(serial, 75)
await client.set_reverb_mod_speed(serial, 40)
await client.set_reverb_mod_depth(serial, 20)
```

### Echo fine parameters

```python
await client.set_echo_feedback(serial, 50)          # 0–100
await client.set_echo_tempo(serial, 120)            # BPM
await client.set_echo_delay_left(serial, 300)       # ms
await client.set_echo_delay_right(serial, 300)      # ms
await client.set_echo_feedback_left(serial, 50)     # 0–100
await client.set_echo_feedback_right(serial, 50)    # 0–100
await client.set_echo_xfb_l_to_r(serial, 0)        # 0–100
await client.set_echo_xfb_r_to_l(serial, 0)        # 0–100
```

### Pitch character

```python
await client.set_pitch_character(serial, 50)        # 0–100
```

### Megaphone details

```python
from goxlrutil_api.protocol.types import MegaphoneStyle

# MegaphoneStyle: Megaphone, Radio, OnThePhone, Overdrive, BuzzCutt, Tweed
await client.set_megaphone_style(serial, MegaphoneStyle.Radio)
await client.set_megaphone_amount(serial, 75)       # 0–100
await client.set_megaphone_post_gain(serial, 3)     # -20..20 dB
```

### Robot details

```python
from goxlrutil_api.protocol.types import RobotStyle, RobotRange

# RobotStyle: Robot1, Robot2, Robot3
await client.set_robot_style(serial, RobotStyle.Robot1)

# RobotRange: Low, Medium, High
await client.set_robot_gain(serial, RobotRange.Low, 0)
await client.set_robot_freq(serial, RobotRange.Low, 80)
await client.set_robot_width(serial, RobotRange.Low, 45)
await client.set_robot_waveform(serial, 0)          # 0–5
await client.set_robot_pulse_width(serial, 50)      # 0–100
await client.set_robot_threshold(serial, -36)
await client.set_robot_dry_mix(serial, 0)
```

### HardTune details

```python
from goxlrutil_api.protocol.types import HardTuneStyle, HardTuneSource

# HardTuneStyle: Natural, Medium, Hard
await client.set_hard_tune_style(serial, HardTuneStyle.Hard)
await client.set_hard_tune_amount(serial, 100)      # 0–100
await client.set_hard_tune_rate(serial, 50)         # 0–100
await client.set_hard_tune_window(serial, 20)       # ms

# HardTuneSource: All, Music, Game, LineIn, System
await client.set_hard_tune_source(serial, HardTuneSource.Music)
```

Read current values from state:

```python
status = await client.get_status()
mixer = status.mixers[serial]
reverb = mixer.effects.current.reverb     # Reverb dataclass
print(reverb.style, reverb.amount)
```

---

## Mic Settings

```python
from goxlrutil_api.protocol.types import MicrophoneType

# Set microphone type (affects input impedance and phantom power)
# MicrophoneType: Dynamic, Condenser, Jack
await client.set_microphone_type(serial, MicrophoneType.Condenser)

# Set hardware gain (0–72 dB; only applies to the active mic type)
await client.set_microphone_gain(serial, MicrophoneType.Condenser, 36)

# Enable/disable the noise gate
await client.set_gate_active(serial, True)

# Set the noise gate threshold (-59–0 dB; lower = more aggressive)
await client.set_gate_threshold(serial, -20)

# Gate detail parameters
from goxlrutil_api.protocol.types import GateTimes

await client.set_gate_attenuation(serial, 100)                # 0–100 %
await client.set_gate_attack(serial, GateTimes.Attack10ms)
await client.set_gate_release(serial, GateTimes.Attack100ms)
```

Read mic settings from state:

```python
mic = status.mixers[serial].mic_status
print(mic.mic_type)                       # MicrophoneType enum
print(mic.noise_gate.enabled)             # bool
print(mic.noise_gate.threshold)           # int (dB)
```

---

## EQ

The GoXLR Full has a 10-band parametric EQ; the GoXLR Mini has a 6-band EQ.

### Full EQ (10-band)

```python
from goxlrutil_api.protocol.types import EqFrequencies

# EqFrequencies: Equalizer31Hz, Equalizer63Hz, Equalizer125Hz, Equalizer250Hz,
#                Equalizer500Hz, Equalizer1KHz, Equalizer2KHz, Equalizer4KHz,
#                Equalizer8KHz, Equalizer16KHz

# Set gain for a band (-9..9 dB)
await client.set_eq_gain(serial, EqFrequencies.Equalizer1KHz, 3)

# Adjust the band center frequency
await client.set_eq_freq(serial, EqFrequencies.Equalizer1KHz, 1100.0)
```

### Mini EQ (6-band)

```python
from goxlrutil_api.protocol.types import MiniEqFrequencies

# MiniEqFrequencies: Equalizer90Hz, Equalizer250Hz, Equalizer500Hz,
#                    Equalizer1KHz, Equalizer3KHz, Equalizer8KHz

await client.set_eq_mini_gain(serial, MiniEqFrequencies.Equalizer1KHz, -2)
await client.set_eq_mini_freq(serial, MiniEqFrequencies.Equalizer1KHz, 950.0)
```

---

## Compressor

```python
from goxlrutil_api.protocol.types import (
    CompressorRatio, CompressorAttackTime, CompressorReleaseTime
)

await client.set_compressor_threshold(serial, -20)              # -40..0 dB
await client.set_compressor_ratio(serial, CompressorRatio.Ratio4to1)
await client.set_compressor_attack(serial, CompressorAttackTime.Attack10ms)
await client.set_compressor_release(serial, CompressorReleaseTime.Release100ms)
await client.set_compressor_makeup_gain(serial, 6)              # 0..24 dB
```

**CompressorRatio values:** `Ratio1to1`, `Ratio1_1to1`, `Ratio1_2to1`, `Ratio1_4to1`, `Ratio1_6to1`,
`Ratio1_8to1`, `Ratio2to1`, `Ratio2_5to1`, `Ratio3to1`, `Ratio3_5to1`, `Ratio4to1`, and more.

---

## De-esser

```python
await client.set_deeser(serial, 30)   # 0–100
```

---

## Scribble Strips

The GoXLR Full has small OLED displays above each fader.

```python
from goxlrutil_api.protocol.types import FaderName

# Set the display text (up to 8 characters)
await client.set_scribble_text(serial, FaderName.A, "MIC")

# Set a number label (shown below the text)
await client.set_scribble_number(serial, FaderName.A, "1")

# Set an icon by name (None clears the icon)
await client.set_scribble_icon(serial, FaderName.A, "mic.png")
await client.set_scribble_icon(serial, FaderName.A, None)   # clear

# Invert the display colours
await client.set_scribble_invert(serial, FaderName.A, True)
```

---

### Monitor and VOD

```python
from goxlrutil_api.protocol.types import VodMode, OutputDevice

# Route the headphone monitor mix through effects
await client.set_monitor_with_fx(serial, True)

# Set the headphone monitor source (which output bus feeds the headphones)
await client.set_monitor_mix(serial, OutputDevice.BroadcastMix)

# VOD (streamer-safe) mode — silences music for stream while keeping it in headphones
# VodMode: Routable, StreamNoMusic
await client.set_vod_mode(serial, VodMode.StreamNoMusic)

# Set the volume used to duck audio when the bleep/swear button is pressed (-34–0 dB)
await client.set_swear_button_volume(serial, -20)

# Percentage variant: 0 % = -34 dB (full duck), 100 % = 0 dB (no ducking)
await client.set_swear_button_volume_pct(serial, 50.0)  # -17 dB
```

### Submix

The submix system allows Mix A (headphones / direct monitor) and Mix B (stream / broadcast) to have independent per-channel volumes.

```python
from goxlrutil_api.protocol.types import ChannelName, OutputDevice, Mix

# Enable the submix system
await client.set_submix_enabled(serial, True)

# Set the Mix B volume for a specific channel (0–255)
await client.set_submix_volume(serial, ChannelName.Music, 128)  # music at 50% on stream

# Link a channel's Mix B volume to its Mix A volume (they move together)
await client.set_submix_linked(serial, ChannelName.Music, True)

# Route an output to Mix A or Mix B
# Mix: A, B
await client.set_submix_output_mix(serial, OutputDevice.BroadcastMix, Mix.B)
```

### Save profile

```python
# Persist all current settings to the active profile
await client.save_profile(serial)
```

---

## Cough Button

```python
from goxlrutil_api.protocol.types import MuteFunction, MuteState

# Set the mute state of the cough button
await client.set_cough_mute_state(serial, MuteState.MutedToAll)

# Configure cough button behaviour
# MuteFunction: All, ToStream, ToVoiceChat, ToPhones, ToLineOut
await client.set_cough_mute_function(serial, MuteFunction.ToStream)

# Hold mode: True = mute while button held, False = toggle on press
await client.set_cough_is_hold(serial, True)
```

---

## Profiles

```python
# List and load profiles (see also Sending Commands → Profiles)
profiles = await client.list_profiles(serial)
await client.load_profile(serial, "Gaming")
await client.load_mic_profile(serial, "StudioMic")

# Persist current settings
await client.save_profile(serial)

# Save as a new profile
await client.save_profile_as(serial, "MyNewProfile")

# Save mic settings (to active mic profile or as new)
await client.save_mic_profile(serial)
await client.save_mic_profile_as(serial, "NewMicProfile")

# Import only the colour settings from another profile
await client.load_profile_colours(serial, "ColoursOnly")

# Rename the active effect preset slot
await client.rename_active_preset(serial, "BrightStar")
```

---

## Sampler Management

```python
from goxlrutil_api.protocol.types import SampleBank, SampleButtons, SamplePlaybackMode, SamplePlayOrder

# Add an audio file to a sampler slot (path on the daemon host)
await client.add_sample(serial, SampleBank.A, SampleButtons.TopLeft, "/home/user/sounds/fx.wav")

# Remove a sample by its index in the slot's list
await client.remove_sample_by_index(serial, SampleBank.A, SampleButtons.TopLeft, 0)

# Trim the in/out points of a sample (0.0–1.0 as fraction of file length)
await client.set_sample_start_percent(serial, SampleBank.A, SampleButtons.TopLeft, 0, 0.1)
await client.set_sample_stop_percent(serial, SampleBank.A, SampleButtons.TopLeft, 0, 0.9)

# Set the playback mode for a slot
# SamplePlaybackMode: PlayNext, StopOnEnd, Loop, SingleLoop, OncePerPress
await client.set_sampler_function(
    serial, SampleBank.A, SampleButtons.TopLeft, SamplePlaybackMode.Loop
)

# Set the order in which samples in a slot are played
# SamplePlayOrder: Sequential, Random
await client.set_sampler_order(
    serial, SampleBank.A, SampleButtons.TopLeft, SamplePlayOrder.Sequential
)

# Global sampler settings
await client.set_sampler_fade_duration(serial, 200)    # fade-out ms
await client.set_sampler_reset_on_clear(serial, True)  # rewind on stop
```

---

## Misc Settings

```python
from goxlrutil_api.protocol.types import DisplayModeComponents, DisplayMode

# Lock all faders to their current positions
await client.set_lock_faders(serial, True)

# When VC is muted, also mute the Chat Mic channel
await client.set_vc_mute_also_mute_cm(serial, True)

# How long a fader button must be held to trigger a mute-hold (ms)
await client.set_mute_hold_duration(serial, 500)

# Change the display mode for a UI component
# DisplayModeComponents: Equaliser, NoiseGate, Compressor
# DisplayMode: Simple, Advanced
await client.set_element_display_mode(
    serial, DisplayModeComponents.Equaliser, DisplayMode.Advanced
)
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
- **Auto-reconnect** is only available with `WebSocketTransport`. `UnixSocketTransport` and `HttpTransport` are request/response only and will raise `ConnectionError` if the daemon is not reachable.
- `long_pressed` fires while the button is still held; a `released` event will follow when the button is let go.
- The serial number changes per physical device. Always discover it via `get_status()` — never hardcode it.
- `client.serials` and `client.get_mixer(serial)` return data from the internal state cache. They are empty/`None` until the first `get_status()` call completes.
- `button_down` only reflects currently-held hardware buttons. Software mute state is tracked separately in `fader_status[fader].mute_state`.

---

## Logging

The library uses the standard Python `logging` module under the `goxlrutil_api` logger hierarchy. Enable debug output to trace all frames sent and received:

```python
import logging
logging.getLogger("goxlrutil_api").setLevel(logging.DEBUG)
```

To silence reconnect noise in production while keeping errors visible:

```python
logging.getLogger("goxlrutil_api").setLevel(logging.WARNING)
```

---

## Importing Callback and State Types

When annotating callbacks or caching state, import the relevant types directly:

```python
from goxlrutil_api import (
    ConnectListener,     # Callable[[], Awaitable[None]]
    DisconnectListener,  # Callable[[], Awaitable[None]]
    MixerStatus,         # dataclass holding per-mixer state
)
from goxlrutil_api.protocol.responses import DaemonStatus
from goxlrutil_api.events import ButtonEvent

async def handle_connect() -> None:
    ...

async def handle_disconnect() -> None:
    ...

async with GoXLRClient(
    transport,
    on_connect=handle_connect,
    on_disconnect=handle_disconnect,
) as client:
    mixer: MixerStatus | None = client.get_mixer(serial)
```
