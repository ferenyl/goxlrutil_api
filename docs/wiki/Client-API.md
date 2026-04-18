# Client API

## GoXLRClient Constructor

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
# Connection is cleanly closed after the block.
```

---

## Methods

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
| `client.serials` | `list[str]` | Serial numbers of all connected mixers (from cache). Requires at least one `get_status()` call. |
| `client.state` | `DaemonState` | Access the live internal state cache. |

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

### Accessing Cached State Without a Network Call

```python
# After connecting, the cache updates on every WebSocket patch.
# Read it at any time without an async call:
mixer = client.state.status.mixers.get(serial)
if mixer:
    mic_vol = mixer.levels.volumes.get("Mic", 0)
```

`get_mixer(serial)` is a shorthand for the above:

```python
async def on_update(status: DaemonStatus) -> None:
    mixer = client.get_mixer(serial)   # zero-latency, no network call
    if mixer:
        vol = mixer.levels.volumes.get("Mic", 0)
        print(f"Mic: {vol}/255")
```

---

## Importing Types

```python
from goxlrutil_api import (
    GoXLRClient,
    WebSocketTransport,
    ConnectListener,     # Callable[[], Awaitable[None]]
    DisconnectListener,  # Callable[[], Awaitable[None]]
    PatchListener,       # Callable[[DaemonStatus], Awaitable[None]]
    ButtonListener,      # Callable[[ButtonEvent], Awaitable[None]]
    MixerStatus,         # dataclass holding per-mixer state
)
from goxlrutil_api.protocol.responses import DaemonStatus
from goxlrutil_api.events import ButtonEvent
```
