---
mode: agent
description: Add or modify GoXLR Python library or demo-webapp functionality
---

Work in this repository using these defaults:

- Python 3.14.4
- Poetry for dependency and packaging management
- `src/` layout
- async-first library design
- GoXLR protocol compatibility must remain exact

When implementing a feature:

1. Identify whether the change belongs in protocol, transport, state handling, public client API, or demo webapp.
2. Reuse the existing GoXLR JSON shapes instead of inventing a new wire format.
3. Keep command sending and event listening decoupled so Unix socket / HTTP can coexist with WebSocket subscriptions.
4. Add or update tests close to the changed behavior.
5. Avoid unsafe demo controls unless the task explicitly requires them.
6. Keep the public package PyPI-friendly: typed API, minimal runtime dependencies, clear module boundaries.

Important protocol reminders:

- Unix socket requests are length-prefixed JSON frames.
- HTTP requests send the same JSON payload to `/api/command`.
- WebSocket requests use `{ "id": ..., "data": ... }`.
- Live daemon updates arrive as JSON Patch events and should update a cached `Status` document.
