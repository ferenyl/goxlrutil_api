"""Abstract transport base class."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable, Coroutine
from typing import Any

from goxlrutil_api.protocol.commands import DaemonRequest
from goxlrutil_api.protocol.responses import DaemonResponse

PatchCallback = Callable[[list[Any]], Coroutine[Any, Any, None]]


class Transport(ABC):
    """Abstract base for all GoXLR daemon transports."""

    @abstractmethod
    async def connect(self) -> None:
        """Establish the connection to the daemon."""

    @abstractmethod
    async def disconnect(self) -> None:
        """Close the connection."""

    @abstractmethod
    async def send(self, request: DaemonRequest) -> DaemonResponse:
        """Send a request and return the response."""

    async def subscribe(self, callback: PatchCallback) -> None:  # noqa: B027
        """
        Subscribe to live patch events.

        The default implementation does nothing; override in transports that
        support push notifications (WebSocket).
        """

    async def __aenter__(self) -> Transport:
        await self.connect()
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.disconnect()
