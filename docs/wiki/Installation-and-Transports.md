# Installation & Transports

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
