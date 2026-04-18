# Copilot instructions for this repository

- Target **Python 3.14.4** and manage the project with **Poetry**.
- Use a **`src/` layout** and keep the publishable library in `src/goxlrutil_api`.
- Design the library as **async-first**. Add sync wrappers only when they clearly improve the public API.
- Preserve the GoXLR wire protocol exactly:
  - Unix socket: `/tmp/goxlr.socket`
  - frame format: 4-byte big-endian length prefix + JSON payload
  - HTTP: `POST /api/command` with the same JSON payload as the socket
  - WebSocket: `/api/websocket` with `{ "id": ..., "data": ... }` envelopes and patch events
- Separate concerns cleanly:
  - protocol serialization
  - transports
  - state cache / patch handling
  - demo webapp

## Library-first principle

- **Fix bugs in the library (`src/goxlrutil_api`), not in the webapp.**
  - If something doesn't work in the demo webapp, the root cause is almost always a missing or incorrect library feature.
  - The webapp (`apps/demo_webapp`) is purely a thin consumer of the library — it should never compensate for library limitations with workarounds.
  - Correct fix order: library → tests → webapp reflects the fix.
- The demo webapp exists to show how the library is used. Its code should read like example usage, not like a place where real logic lives.

## General guidelines

- Prefer **small typed helpers** over broad untyped dictionaries in the public API.
- Do not hardcode device serial numbers outside of fixtures or local experiments.
- Keep the demo webapp safe by default: connection status, read-only inspection, and a limited set of reversible write actions first.
- Tests should default to mocks / fixtures. Live-daemon integration tests must be **explicitly opt-in**.
- Use modern Python style: type hints everywhere, `pathlib`, `enum`, `dataclasses` or similarly explicit models, and clear exception types.
- Prefer `ruff`, `pytest`, and `pyright` for linting, tests, and static typing unless the repo establishes a different standard later.
