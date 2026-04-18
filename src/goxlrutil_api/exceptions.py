"""GoXLR Utility API – custom exception hierarchy."""

from __future__ import annotations


class GoXLRError(Exception):
    """Base exception for all goxlrutil_api errors."""


class ConnectionError(GoXLRError):
    """Raised when a transport cannot connect or loses its connection."""


class ProtocolError(GoXLRError):
    """Raised when a message cannot be serialised/deserialised."""


class CommandError(GoXLRError):
    """Raised when the daemon returns an error response to a command."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message
