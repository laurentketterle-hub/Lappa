"""IDE launch bridge: start/stop ros2 launch from IDE and stream logs to console.

This module wraps :mod:`lappa.docker_bridge` with a higher-level session API
suitable for embedding in a Qt IDE, web dashboard, or automation pipeline.
It also exposes a native-fallback path via ``lappa sim`` when Docker is
unavailable.
"""

from __future__ import annotations

import time
from collections.abc import Iterator
from typing import Any

from lappa import docker_bridge
from lappa.config import DEMOS_ROOT
from lappa.sim.session import SESSION


class LaunchSession:
    """High-level launch session usable from an IDE action button or script."""

    def __init__(
        self,
        demo: str,
        *,
        prefer_docker: bool = True,
        rebuild: bool = True,
        skip_docker: bool = False,
    ) -> None:
        self._demo = demo.strip()
        if not self._demo:
            raise ValueError("demo name required")
        self._prefer_docker = prefer_docker
        self._rebuild = rebuild
        self._skip_docker = skip_docker
        self._started: bool = False
        self._native: bool = False
        self._last_result: dict[str, Any] = {}

    def start(self) -> dict[str, Any]:
        """Start a launch session (Docker or native fallback)."""
        if self._started:
            self.stop()

        docker_bridge.clear_launch_logs()
        result: dict[str, Any]

        if self._skip_docker:
            result = self._start_native()
        elif self._prefer_docker and docker_bridge.docker_available():
            result = self._start_docker()
            if not result.get("ok"):
                docker_bridge.record_native_log(
                    f"Docker launch failed, falling back to native sim: {result.get('error','')}"
                )
                native = self._start_native()
                native["docker_fallback"] = True
                native["docker_error"] = result.get("error", "")
                result = native
        else:
            if self._prefer_docker and not docker_bridge.docker_available():
                docker_bridge.record_native_log(
                    "Docker not available -- using native kinematics simulation"
                )
            result = self._start_native()

        self._started = result.get("ok", False)
        self._native = result.get("mode") == "native"
        self._last_result = result
        return result

    def stop(self) -> dict[str, Any]:
        """Stop the current launch session (Docker or native)."""
        if not self._started:
            return {"ok": True, "stopped": False, "reason": "not started"}

        docker_stopped: dict[str, Any] = {"ok": True}
        native_stopped: dict[str, Any] = {"ok": True}

        try:
            docker_stopped = docker_bridge.stop_launch()
        except Exception:
            pass
        try:
            native_stopped = SESSION.stop()
        except Exception:
            pass

        self._started = False
        self._native = False
        self._last_result = {}

        return {
            "ok": True,
            "stopped": True,
            "native_stopped": bool(native_stopped.get("ok")),
            "docker_stopped": bool(docker_stopped.get("ok")),
        }

    def status(self) -> dict[str, Any]:
        """Return combined Docker + native status summary."""
        docker_status = docker_bridge.status()
        native_sim = SESSION.status()
        return {
            "demo": self._demo,
            "started": self._started,
            "native": self._native,
            "docker": {
                "available": docker_status.get("available"),
                "daemon": docker_status.get("daemon"),
                "container_running": docker_status.get("running"),
                "session_mode": docker_status.get("session", {}).get("mode"),
            },
            "native_sim": {
                "running": native_sim.get("state", {}).get("running"),
                "demo": native_sim.get("demo"),
            },
            "last_result": self._last_result,
        }

    def poll_logs(self, after: int = 0, limit: int = 200) -> list[dict[str, Any]]:
        """Return log events since *after* cursor."""
        data = docker_bridge.launch_logs(after=after, limit=limit)
        return data.get("events", [])

    def stream_console(self, *, heartbeat_interval: float = 0.5) -> Iterator[dict[str, Any]]:
        """Generator yielding log events in near-real-time."""
        after = 0
        while self._started:
            events = self.poll_logs(after=after)
            if events:
                for event in events:
                    yield event
                after = events[-1]["seq"]
            else:
                yield {"stream": "heartbeat", "time": time.time()}
                time.sleep(heartbeat_interval)

    def run_to_completion(self, timeout: float = 30.0) -> dict[str, Any]:
        """Start, collect logs for *timeout* seconds, then stop."""
        result = self.start()
        if not result.get("ok"):
            return result

        collected: list[dict[str, Any]] = []
        after = 0
        deadline = time.time() + timeout
        while time.time() < deadline:
            events = self.poll_logs(after=after)
            if events:
                collected.extend(events)
                after = events[-1]["seq"]
            time.sleep(0.2)

        stop_result = self.stop()
        return {
            "ok": True,
            "demo": self._demo,
            "native": self._native,
            "logs": collected,
            "stop": stop_result,
        }

    def _start_docker(self) -> dict[str, Any]:
        docker_bridge.record_native_log(f"IDE launch: ros2 launch {self._demo} (Docker)")
        result = docker_bridge.launch_demo(self._demo, ensure_up=True, rebuild=self._rebuild)
        result["mode"] = "docker"
        return result

    def _start_native(self) -> dict[str, Any]:
        demo_path = DEMOS_ROOT / self._demo
        if not demo_path.is_dir():
            return {"ok": False, "mode": "native", "error": f"unknown demo package: {self._demo}"}
        docker_bridge.record_native_log(f"IDE launch: native kinematics sim {self._demo}")
        out = SESSION.start(self._demo, demo_path)
        return {"ok": bool(out.get("state", {}).get("running")), "mode": "native", "demo": self._demo, "sim_output": out}


def ide_launch(demo: str, *, prefer_docker: bool = True, rebuild: bool = True) -> dict[str, Any]:
    """One-shot: start a launch session and return initial status + logs."""
    session = LaunchSession(demo, prefer_docker=prefer_docker, rebuild=rebuild)
    result = session.start()
    logs = session.poll_logs(after=0)
    result["initial_logs"] = logs
    return result


def ide_stop(demo: str = "") -> dict[str, Any]:
    """Stop all launch activity (Docker + native)."""
    return LaunchSession(demo or "any").stop()
