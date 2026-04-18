"""Tests for DaemonState and JSON Patch application."""

from __future__ import annotations

from goxlrutil_api.state import DaemonState


def test_initial_state_is_empty(raw_status: dict) -> None:
    state = DaemonState()
    assert state.status.mixers == {}


def test_set_raw_parses_status(raw_status: dict) -> None:
    state = DaemonState()
    state.set_raw(raw_status)
    assert "TEST_SERIAL_001" in state.status.mixers


def test_mixer_volume_from_fixture(raw_status: dict) -> None:
    state = DaemonState()
    state.set_raw(raw_status)
    mixer = state.status.mixers["TEST_SERIAL_001"]
    assert mixer.levels.volumes["Mic"] == 200


def test_apply_patch_updates_volume(raw_status: dict) -> None:
    state = DaemonState()
    state.set_raw(raw_status)

    ops = [
        {
            "op": "replace",
            "path": "/mixers/TEST_SERIAL_001/levels/volumes/Mic",
            "value": 100,
        }
    ]
    state.apply_patch(ops)
    assert state.status.mixers["TEST_SERIAL_001"].levels.volumes["Mic"] == 100


def test_apply_patch_before_status_is_ignored() -> None:
    state = DaemonState()
    # Should not raise even though _raw is empty
    state.apply_patch([{"op": "replace", "path": "/config/log_level", "value": "Debug"}])


def test_apply_invalid_patch_logs_warning(raw_status: dict) -> None:
    state = DaemonState()
    state.set_raw(raw_status)
    # Invalid path – should not raise, just log
    state.apply_patch([{"op": "replace", "path": "/nonexistent/deep/path", "value": 1}])


def test_daemon_version_from_fixture(raw_status: dict) -> None:
    state = DaemonState()
    state.set_raw(raw_status)
    assert state.status.config.daemon_version == "1.0.0"


def test_fader_status_from_fixture(raw_status: dict) -> None:
    state = DaemonState()
    state.set_raw(raw_status)
    mixer = state.status.mixers["TEST_SERIAL_001"]
    assert mixer.fader_status["A"].channel.value == "Mic"
