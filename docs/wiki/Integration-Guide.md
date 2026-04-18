# Integration Guide

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

    # Long-press Fader1Mute to trigger custom action
    if (
        event.button_enum == Button.Fader1Mute
        and event.event_type == ButtonEventType.long_pressed
    ):
        print(f"[{serial}] Long-press detected")


async def main() -> None:
    transport = WebSocketTransport("ws://localhost:14564/api/websocket")

    try:
        async with GoXLRClient(
            transport,
            on_state_update=on_state_update,
            on_button_event=on_button_event,
            long_press_threshold=0.8,
        ) as client:
            status = await client.get_status()
            serial = next(iter(status.mixers))
            mixer = status.mixers[serial]

            print(f"Connected: {mixer.hardware.device_type.value} [{serial}]")
            print(f"Profile: {mixer.profile_name}")

            await client.set_volume(serial, ChannelName.Headphones, 220)

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

## Protocol Notes

These details are useful when extending the library or debugging.

### Wire Format

| Transport | Format |
|---|---|
| Unix socket | 4-byte big-endian `uint32` length prefix + UTF-8 JSON payload. |
| HTTP | `POST /api/command` with JSON body, returns JSON response. |
| WebSocket | Messages are `{"id": <uint64>, "data": <request/response>}`. Unsolicited patch events arrive as `{"id": 0, "data": {"Patch": [<ops>]}}`. |

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

Patch operations use paths rooted at the `Status` object:

```json
{"op": "replace", "path": "/mixers/S210400463CQK/button_down/Bleep", "value": true}
{"op": "replace", "path": "/mixers/S210400463CQK/levels/volumes/Mic", "value": 200}
{"op": "replace", "path": "/mixers/S210400463CQK/fader_status/A/mute_state", "value": "MutedToAll"}
```

### Important Constraints

- Button events **require** WebSocket transport.
- Auto-reconnect is only available with `WebSocketTransport`.
- `long_pressed` fires while the button is still held; a `released` event follows when the button is released.
- Always discover the serial number via `get_status()` — never hardcode it.
- `client.serials` and `client.get_mixer(serial)` return data from the internal state cache and are empty/`None` until the first `get_status()` call completes.
- `button_down` only reflects currently-held hardware buttons. Software mute state is tracked separately in `fader_status[fader].mute_state`.

---

## Logging

The library uses the standard Python `logging` module under the `goxlrutil_api` logger hierarchy.

```python
import logging

# Enable debug output to trace all frames sent and received
logging.getLogger("goxlrutil_api").setLevel(logging.DEBUG)

# Silence reconnect noise in production while keeping errors visible
logging.getLogger("goxlrutil_api").setLevel(logging.WARNING)
```

---

## Importing Callback and State Types

```python
from goxlrutil_api import (
    ConnectListener,     # Callable[[], Awaitable[None]]
    DisconnectListener,  # Callable[[], Awaitable[None]]
    PatchListener,       # Callable[[DaemonStatus], Awaitable[None]]
    ButtonListener,      # Callable[[ButtonEvent], Awaitable[None]]
    MixerStatus,         # dataclass holding per-mixer state
)
from goxlrutil_api.protocol.responses import DaemonStatus
from goxlrutil_api.events import ButtonEvent
```
