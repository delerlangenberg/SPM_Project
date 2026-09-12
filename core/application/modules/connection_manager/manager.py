"""Stable connection lifecycle for native SPM Operator clients."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from threading import RLock
from typing import Any, Callable


Payload = dict[str, Any]


@dataclass(frozen=True, slots=True)
class ConnectionStatus:
    state: str = "disconnected"
    connected: bool = False
    busy: bool = False
    port: str = ""
    message: str = "Not connected."
    payload: Payload = field(default_factory=dict)


class ConnectionManager:
    """Own connect/disconnect state while delegating hardware I/O to a backend."""

    def __init__(
        self,
        *,
        connect_backend: Callable[..., Payload] | None = None,
        disconnect_backend: Callable[[], Payload] | None = None,
        apply_port: Callable[[str], Any] | None = None,
    ) -> None:
        if connect_backend is None or disconnect_backend is None or apply_port is None:
            from core.web.system_control import system_apply_port, system_disconnect, system_on

            connect_backend = connect_backend or system_on
            disconnect_backend = disconnect_backend or system_disconnect
            apply_port = apply_port or system_apply_port
        self._connect_backend = connect_backend
        self._disconnect_backend = disconnect_backend
        self._apply_port = apply_port
        self._status = ConnectionStatus()
        self._simulation_active = False
        self._lock = RLock()

    def connect(self, port: str = "") -> Payload:
        """Connect in hardware read-only mode; never authorizes physical motion."""
        with self._lock:
            if self._simulation_active:
                payload = {"ok": True, "connected": False, "ready": True, "status": "simulation",
                           "mode": "simulation", "port": "VIRTUAL", "message": "Simulation Mode ready; no serial port opened."}
                self._status = ConnectionStatus(state="simulation", connected=False, busy=False, port="VIRTUAL",
                                                message=payload["message"], payload=payload)
                return dict(payload)
            if self._status.busy:
                return self._busy_payload()
            if self._status.connected:
                return dict(self._status.payload)
            self._status = ConnectionStatus(state="connecting", busy=True, port=port, message="Connecting…")

        # This gate controls read-only M115/M119/M105/M114 queries only. Motion
        # remains protected by the independent authorization module gates.
        try:
            if os.environ.get("SPM_WEB_ALLOW_READONLY_HARDWARE", "1") == "0":
                raise PermissionError(
                    "Read-only hardware access is disabled for this session."
                )
            os.environ["SPM_WEB_ALLOW_READONLY_HARDWARE"] = "1"
            port_result = self._apply_port(port)
            if isinstance(port_result, dict) and not port_result.get("ok"):
                return self.accept_payload({
                    **port_result,
                    "ok": False,
                    "connected": False,
                    "powered": False,
                    "ready": False,
                    "status": "failed",
                    "port": port,
                })
            payload = dict(self._connect_backend(mode="hardware_readonly", port=port))
        except Exception as exc:
            payload = {"ok": False, "connected": False, "status": "failed", "message": str(exc), "port": port}
        return self.accept_payload(payload)

    def disconnect(self) -> Payload:
        with self._lock:
            if self._status.busy:
                return self._busy_payload()
            self._status = ConnectionStatus(
                state="disconnecting",
                connected=self._status.connected,
                busy=True,
                port=self._status.port,
                message="Disconnecting…",
                payload=self._status.payload,
            )
        try:
            payload = dict(self._disconnect_backend())
        except Exception as exc:
            payload = {"ok": False, "connected": True, "status": "failed", "message": str(exc)}
        return self.accept_payload(payload)

    def accept_payload(self, payload: Payload) -> Payload:
        """Update lifecycle state from a backend result and return a safe copy."""
        result = dict(payload)
        backend_state = str(result.get("status", "unknown"))
        if "connected" in result:
            connected = bool(result["connected"])
        else:
            connected = bool(result.get("powered") or result.get("ready"))
        connected = connected and backend_state != "disconnected"
        if backend_state == "failed" and self._status.state == "disconnecting":
            connected = True
        state = "connected" if connected else ("disconnected" if backend_state == "disconnected" else "failed")
        with self._lock:
            self._status = ConnectionStatus(
                state=state,
                connected=connected,
                busy=False,
                port=str(result.get("port") or self._status.port),
                message=str(result.get("message") or backend_state),
                payload=result,
            )
        return dict(result)

    def getStatus(self) -> ConnectionStatus:  # noqa: N802 - required stable interface
        with self._lock:
            status = self._status
            return ConnectionStatus(
                state=status.state,
                connected=status.connected,
                busy=status.busy,
                port=status.port,
                message=status.message,
                payload=dict(status.payload),
            )

    def get_status(self) -> ConnectionStatus:
        return self.getStatus()

    def set_simulation_mode(self, enabled: bool) -> ConnectionStatus:
        """Select virtual routing without opening or closing any serial port."""
        with self._lock:
            self._simulation_active = bool(enabled)
            if enabled and not self._status.connected:
                self._status = ConnectionStatus(
                    state="simulation", connected=False, port="VIRTUAL",
                    message="Simulation Mode ready; no serial port opened.",
                    payload={"ok": True, "ready": True, "status": "simulation", "mode": "simulation", "port": "VIRTUAL"},
                )
            elif not enabled and self._status.state == "simulation":
                self._status = ConnectionStatus()
            return self.getStatus()

    def _busy_payload(self) -> Payload:
        return {
            "ok": False,
            "connected": self._status.connected,
            "status": "busy",
            "message": "A connection operation is already running.",
            "port": self._status.port,
        }
