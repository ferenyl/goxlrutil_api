# goxlrutil-api

Async Python library for communicating with the
[GoXLR Utility daemon](https://github.com/GoXLR-on-Linux/goxlr-utility).

## Features

- **Three transports:** Unix socket, HTTP, WebSocket
- **Async-first** with optional sync wrappers
- **Live state cache:** incoming JSON Patch events are applied automatically
- **Typed API:** `dataclass`/`enum` models for all commands and responses

## Installation

```bash
pip install goxlrutil-api
# With demo webapp extras:
pip install "goxlrutil-api[webapp]"
```

## Quick start

```python
import asyncio
from goxlrutil_api import GoXLRClient
from goxlrutil_api.transport import UnixSocketTransport

async def main():
    transport = UnixSocketTransport()
    async with GoXLRClient(transport) as client:
        status = await client.get_status()
        for serial, mixer in status.mixers.items():
            print(serial, mixer.hardware.device_type)

asyncio.run(main())
```

## Transports

| Class | Usage |
|---|---|
| `UnixSocketTransport` | Local daemon via `/tmp/goxlr.socket` |
| `HttpTransport` | HTTP `POST /api/command` (local or remote) |
| `WebSocketTransport` | WebSocket `/api/websocket` – also receives live Patch events |

## Demo webapp

```bash
# With Poetry (development):
poetry install --all-extras
poetry run uvicorn apps.demo_webapp.main:app --reload

# Or with pip:
pip install "goxlrutil-api[webapp]"
uvicorn apps.demo_webapp.main:app --reload
```

Open http://localhost:8000

By default the webapp connects via Unix socket (`/tmp/goxlr.socket`).
To use WebSocket instead (enables live patch events):

```bash
GOXLR_USE_WS=1 poetry run uvicorn apps.demo_webapp.main:app --reload
```

The app starts even if the GoXLR daemon is not running – it will show a "not connected" status.

## Development

```bash
poetry install
poetry run pytest
poetry run ruff check src
poetry run pyright
```

## Protocol notes

- Unix socket uses a **4-byte big-endian** length-prefixed JSON frame.
- HTTP sends the same `DaemonRequest` JSON to `POST /api/command`.
- WebSocket wraps requests in `{"id": <uint>, "data": <DaemonRequest>}`.
- State updates from WebSocket are RFC 6902 JSON Patch operations.
