"""Tests for Unix socket frame encoding/decoding."""

from __future__ import annotations

import struct

from goxlrutil_api.transport.socket import _HEADER


def encode_frame(payload: bytes) -> bytes:
    return _HEADER.pack(len(payload)) + payload


def test_header_is_big_endian_4_bytes() -> None:
    assert _HEADER.format == ">I"
    assert _HEADER.size == 4


def test_encode_frame_length_prefix() -> None:
    payload = b'{"Ping":null}'
    frame = encode_frame(payload)
    length = struct.unpack(">I", frame[:4])[0]
    assert length == len(payload)
    assert frame[4:] == payload


def test_roundtrip_large_payload() -> None:
    payload = b"x" * 65536
    frame = encode_frame(payload)
    length = struct.unpack(">I", frame[:4])[0]
    assert length == 65536


def test_encode_frame_empty_payload() -> None:
    frame = encode_frame(b"")
    assert struct.unpack(">I", frame[:4])[0] == 0
    assert len(frame) == 4
