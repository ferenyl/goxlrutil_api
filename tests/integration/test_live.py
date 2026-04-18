"""
Live integration tests – only run when GOXLR_LIVE_TEST=1 is set.

Usage:
    GOXLR_LIVE_TEST=1 poetry run pytest tests/integration/
"""

from __future__ import annotations

import os

import pytest

from goxlrutil_api import GoXLRClient, UnixSocketTransport

pytestmark = pytest.mark.skipif(
    os.getenv("GOXLR_LIVE_TEST") != "1",
    reason="Set GOXLR_LIVE_TEST=1 to run live daemon tests",
)


@pytest.mark.asyncio
async def test_ping_live() -> None:
    transport = UnixSocketTransport()
    async with GoXLRClient(transport) as client:
        assert await client.ping()


@pytest.mark.asyncio
async def test_get_status_live() -> None:
    transport = UnixSocketTransport()
    async with GoXLRClient(transport) as client:
        status = await client.get_status()
        assert len(status.mixers) > 0
        for serial, mixer in status.mixers.items():
            assert serial
            assert mixer.hardware.serial_number == serial
