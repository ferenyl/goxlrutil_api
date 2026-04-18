"""DaemonState – cached copy of DaemonStatus with JSON Patch support."""

from __future__ import annotations

import logging
from typing import Any, cast

import jsonpatch  # type: ignore[import-untyped]

from goxlrutil_api.protocol.responses import DaemonStatus, parse_status

_log = logging.getLogger(__name__)


class DaemonState:
    """
    Holds a local copy of the daemon's status document.

    Call `update(status)` when a full Status response arrives.
    Call `apply_patch(ops)` for each incoming Patch event.
    The raw dict is always kept in sync so patches can be applied accurately,
    while `status` exposes the typed view.
    """

    def __init__(self) -> None:
        self._raw: dict[str, Any] = {}
        self._status: DaemonStatus = DaemonStatus()

    @property
    def status(self) -> DaemonStatus:
        return self._status

    def update(self, status: DaemonStatus) -> None:
        """Replace the typed status view (does not update the raw patch dict)."""
        self._status = status

    def apply_patch(self, ops: list[Any]) -> None:
        """Apply a list of RFC 6902 JSON Patch operations to the cached state."""
        if not self._raw:
            _log.debug("Received patch before initial status – ignoring")
            return
        try:
            patch = jsonpatch.JsonPatch(ops)
            result = cast(dict[str, Any], patch.apply(self._raw))  # type: ignore[no-untyped-call]
            self._raw = result
            self._status = parse_status(self._raw)
        except Exception as exc:
            _log.warning("Failed to apply patch: %s", exc)

    def set_raw(self, raw: dict[str, Any]) -> None:
        """Store the raw status dict (called after a GetStatus response)."""
        self._raw = raw
        self._status = parse_status(raw)
