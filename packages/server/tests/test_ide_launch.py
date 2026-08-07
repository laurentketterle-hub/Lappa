"""Tests for the IDE launch bridge (no Docker required)."""

import time

import pytest

from lappa.ide_launch import LaunchSession, ide_launch, ide_stop


def test_launch_session_requires_demo():
    with pytest.raises(ValueError, match="demo name required"):
        LaunchSession("")


def test_launch_session_creation():
    session = LaunchSession("diff_drive_2w")
    assert session._demo == "diff_drive_2w"
    assert session._prefer_docker is True
    assert session._skip_docker is False


def test_skip_docker_uses_native():
    """With skip_docker=True, Docker is never called."""
    session = LaunchSession("diff_drive_2w", skip_docker=True)
    result = session.start()
    assert result["mode"] == "native"
    assert result.get("ok") is True
    assert session._native is True
    session.stop()


def test_stop_before_start_is_noop():
    session = LaunchSession("diff_drive_2w")
    result = session.stop()
    assert result["stopped"] is False
    assert result.get("reason") == "not started"


def test_native_start_stop():
    session = LaunchSession("diff_drive_2w", skip_docker=True)
    result = session.start()
    assert result["ok"] is True
    assert session.status()["started"] is True

    stop_result = session.stop()
    assert stop_result["stopped"] is True
    assert session.status()["started"] is False


def test_poll_logs_returns_list():
    session = LaunchSession("diff_drive_2w", skip_docker=True)
    session.start()
    events = session.poll_logs(after=0)
    assert isinstance(events, list)
    session.stop()


def test_status_shape():
    session = LaunchSession("diff_drive_2w", skip_docker=True)
    session.start()
    st = session.status()
    assert "demo" in st
    assert "started" in st
    assert "native" in st
    assert "docker" in st
    assert "native_sim" in st
    session.stop()


def test_run_to_completion():
    session = LaunchSession("diff_drive_2w", skip_docker=True)
    result = session.run_to_completion(timeout=2.0)
    assert result["ok"] is True
    assert result["demo"] == "diff_drive_2w"
    assert "logs" in result
    assert "stop" in result
    assert session._started is False


def test_ide_launch_convenience():
    result = ide_launch("diff_drive_2w", prefer_docker=False)
    assert result.get("ok") is True
    assert "initial_logs" in result
    ide_stop()


def test_ide_stop():
    """ide_stop creates its own session; since nothing is started it is a no-op.
    For actual stop, call stop() on the same LaunchSession instance."""
    result = ide_stop()
    # No session was started, so it reports not-stopped
    assert result.get("stopped") is False
    assert result.get("reason") == "not started"
    # ide_launch creates a local session; verify it can start and stop on its own
    session = LaunchSession("diff_drive_2w", skip_docker=True)
    session.start()
    assert session._started is True
    stop_result = session.stop()
    assert stop_result["stopped"] is True


def test_unknown_demo_native():
    session = LaunchSession("no_such_package_xyz", skip_docker=True)
    result = session.start()
    assert result["ok"] is False
    assert "unknown" in result.get("error", "").lower()


def test_prefer_docker_graceful_fallback(monkeypatch):
    """When Docker is available but launch fails, fall back to native."""
    monkeypatch.setattr("lappa.ide_launch.docker_bridge.docker_available", lambda: True)

    # Simulate Docker launch failure
    def fake_launch(demo, ensure_up=True, rebuild=True):
        return {"ok": False, "error": "container not running"}

    monkeypatch.setattr("lappa.ide_launch.docker_bridge.launch_demo", fake_launch)

    session = LaunchSession("diff_drive_2w")
    result = session.start()

    assert result.get("mode") == "native"
    assert result.get("docker_fallback") is True
    assert "docker_error" in result
    session.stop()


def test_session_restart_stops_previous():
    session = LaunchSession("diff_drive_2w", skip_docker=True)
    session.start()
    assert session._started is True
    # Starting again should stop previous first
    session.start()
    assert session._started is True
    session.stop()
