# goxlrutil_api – Projektplan

## Syfte

Bygga ett Python-bibliotek (`goxlrutil_api`) som kommunicerar med
[goxlr-utility-daemonen](https://github.com/GoXLR-on-Linux/goxlr-utility) via Unix
socket, HTTP eller WebSocket. Biblioteket ska kunna publiceras till PyPI och hanteras
med Poetry. En demo-webapp i FastAPI används som interaktivt testverktyg.

---

## Protokoll (härlett från Rust-källkoden)

| Transport | Detaljer |
|-----------|---------|
| Unix socket | `/tmp/goxlr.socket` · 4-byte **big-endian** längd-prefix + JSON-payload |
| HTTP | `POST http://localhost:{port}/api/command` med `DaemonRequest` som JSON-body |
| WebSocket | `ws://localhost:{port}/api/websocket` · frames: `{"id": uint, "data": DaemonRequest}` |

- **Requests:** `DaemonRequest` (Ping, GetStatus, Command(serial, GoXLRCommand), …)
- **Responses:** `DaemonResponse` (Ok, Error, Status(DaemonStatus), Patch, MicLevel)
- **State-uppdateringar** via WebSocket levereras som RFC 6902 JSON Patch-events

---

## Projektstruktur

```
goxlrutil_api/
├── .python-version                  → 3.14.4
├── .github/
│   ├── copilot-instructions.md
│   └── prompts/
│       └── goxlr-python-feature.prompt.md
├── pyproject.toml                   Poetry + ruff + pyright-konfiguration
├── README.md
├── PLAN.md                          Den här filen
├── src/
│   └── goxlrutil_api/
│       ├── __init__.py              Publika re-exporter
│       ├── exceptions.py            GoXLRError, ConnectionError, CommandError
│       ├── protocol/
│       │   ├── __init__.py
│       │   ├── types.py             Enums: FaderName, ChannelName, MuteFunction, …
│       │   ├── commands.py          DaemonRequest, DaemonCommand, GoXLRCommand
│       │   └── responses.py         DaemonResponse, DaemonStatus, MixerStatus, …
│       ├── transport/
│       │   ├── __init__.py
│       │   ├── base.py              Abstrakt Transport-ABC
│       │   ├── socket.py            Unix socket-transport
│       │   ├── http.py              HTTP-transport (httpx)
│       │   └── websocket.py         WebSocket-transport (skickar + lyssnar)
│       ├── state.py                 DaemonState: cachad status + JSON patch apply
│       ├── client.py                GoXLRClient: hög-nivå async-API
│       └── sync.py                  Sync-wrappers (run_sync-helper)
├── apps/
│   └── demo_webapp/
│       ├── __init__.py
│       ├── main.py                  FastAPI-app
│       ├── templates/index.html     Jinja2 + HTMX-UI
│       └── static/style.css
└── tests/
    ├── conftest.py
    ├── fixtures/
    │   └── status_example.json      Inspelad DaemonStatus för tester
    ├── unit/
    │   ├── test_framing.py          Socket-framing encode/decode
    │   ├── test_commands.py         Command-serialisering round-trips
    │   └── test_state_patch.py      JSON patch apply
    └── integration/                 Opt-in: GOXLR_LIVE_TEST=1
        └── test_live.py
```

---

## Todos

| # | ID | Titel | Beroenden |
|---|-----|-------|-----------|
| 1 | `scaffold` | Poetry-scaffold, pyproject.toml, README | – |
| 2 | `protocol-types` | Enums/dataclasses – types.py | scaffold |
| 3 | `protocol-cmds` | DaemonRequest, GoXLRCommand – commands.py | protocol-types |
| 4 | `protocol-resp` | DaemonResponse, DaemonStatus, … – responses.py | protocol-types |
| 5 | `exceptions` | GoXLRError, ConnectionError, CommandError | scaffold |
| 6 | `transport-base` | Abstrakt Transport-ABC | exceptions |
| 7 | `transport-socket` | Unix socket med 4-byte big-endian framing | transport-base, protocol-cmds, protocol-resp |
| 8 | `transport-http` | HTTP via httpx | transport-base, protocol-cmds, protocol-resp |
| 9 | `transport-ws` | WebSocket med `{id, data}`-envelopes + Patch-lyssnare | transport-base, protocol-cmds, protocol-resp |
| 10 | `state` | DaemonState + apply_patch() | protocol-resp |
| 11 | `client` | GoXLRClient (async hög-nivå API) | transport-base, state |
| 12 | `sync-wrappers` | run_sync() + GoXLRClientSync | client |
| 13 | `tests-unit` | pytest-tester (mock/fixture, inga live-anslutningar) | client |
| 14 | `demo-webapp` | FastAPI + Jinja2 + HTMX demo | client |
| 15 | `ci` | GitHub Actions: ruff, pyright, pytest | tests-unit |

---

## Designbeslut

- **Async-first:** Allt i `src/goxlrutil_api` är async. Sync-wrappers är ett tunt
  skal ovanpå.
- **Transportabstraktion:** `Transport`-ABC gör det enkelt att byta mellan socket,
  HTTP och WebSocket utan att ändra klient-koden.
- **State-cache:** `DaemonState` håller en lokal kopia av `DaemonStatus` och
  tillämpar inkommande JSON Patch-events, så att läsare alltid ser senast kända
  tillstånd utan extra round-trips.
- **PyPI-vänlig:** Minimala runtime-beroenden (`httpx`, `jsonpatch`). Webapp-deps
  (`fastapi`, `uvicorn`, `jinja2`) är valfria extras.
- **Tester:** Unit-tester kör mot mock/fixtures. Levande integrationstester kräver
  `GOXLR_LIVE_TEST=1` och en körande daemon.
- **Säkerhet i demo-appen:** Anslutningsstatus och read-only-visning är
  standardläge. Skrivoperationer (volym, mute) är begränsade och reversibla.
