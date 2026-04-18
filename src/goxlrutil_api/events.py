"""Button event types for the GoXLR Utility library."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from goxlrutil_api.protocol.types import Button


class ButtonEventType(str, Enum):
    pressed = "pressed"
    released = "released"
    long_pressed = "long_pressed"


@dataclass
class ButtonEvent:
    """A button press, release, or long-press event from a GoXLR device.

    ``button`` is always the raw string key from the daemon (e.g. ``"Bleep"``).
    ``button_enum`` is the parsed :class:`Button` enum, or ``None`` for unknown buttons.
    ``held_seconds`` is populated for ``released`` and ``long_pressed`` events.

    .. note::
        Button events require a :class:`~goxlrutil_api.transport.WebSocketTransport`
        because the daemon pushes button state changes as JSON Patch events.
        With :class:`~goxlrutil_api.transport.UnixSocketTransport`, ``button_down``
        in the state is only updated on explicit :meth:`~GoXLRClient.get_status` calls.
    """

    serial: str
    button: str
    event_type: ButtonEventType
    button_enum: Button | None = field(default=None, compare=False)
    held_seconds: float = 0.0

    @staticmethod
    def from_raw(
        serial: str,
        btn_name: str,
        event_type: ButtonEventType,
        held_seconds: float = 0.0,
    ) -> ButtonEvent:
        try:
            btn_enum: Button | None = Button(btn_name)
        except ValueError:
            btn_enum = None
        return ButtonEvent(
            serial=serial,
            button=btn_name,
            event_type=event_type,
            button_enum=btn_enum,
            held_seconds=held_seconds,
        )
