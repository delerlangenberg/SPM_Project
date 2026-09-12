"""Stage 6 — Deterministic Hardware Safety Gate.

Enforces:
- Centralized physical command authority.
- Hard coordinate bounding and safe Z floor limits.
- Mandatory Arduino feedback freshness / watchdog fault-latching.
- Immediate motion cancellation and non-auto-recovering fault states.
- Absolute rejection of unverified homing (G28), bed probing (G29), and thermal commands.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import math
import re
from threading import RLock
from typing import Any, Optional


class GateState(str, Enum):
    DISCONNECTED = "DISCONNECTED"
    READ_ONLY = "READ_ONLY"
    PREFLIGHT = "PREFLIGHT"
    READY = "READY"
    ARMED = "ARMED"
    MOTION_AUTHORIZED = "MOTION_AUTHORIZED"
    FAULT = "FAULT"
    E_STOP = "E_STOP"


@dataclass(frozen=True)
class CoordinateLimits:
    x_min_mm: float = 20.0
    x_max_mm: float = 80.0
    y_min_mm: float = 20.0
    y_max_mm: float = 80.0
    z_min_floor_mm: float = 120.0  # Safe high Z floor pending physical commissioning
    z_max_mm: float = 150.0
    max_feedrate_xy_mm_s: float = 50.0
    max_feedrate_z_mm_s: float = 10.0


@dataclass(frozen=True)
class GateEvent:
    timestamp: str
    event: str
    from_state: GateState
    to_state: GateState
    detail: str


class DeterministicHardwareSafetyGate:
    """Deterministic, enforceable hardware safety authority."""

    FORBIDDEN_GCODE = (
        "G28", "G29", "M17", "M18", "M80", "M81",
        "M104", "M109", "M140", "M190", "M302", "M500", "M501", "M502",
    )

    def __init__(
        self,
        limits: CoordinateLimits = CoordinateLimits(),
        feedback_deadline_s: float = 0.25,
    ) -> None:
        self._lock = RLock()
        self._state = GateState.DISCONNECTED
        self._limits = limits
        self._feedback_deadline_s = feedback_deadline_s
        self._last_arduino_feedback_monotonic: Optional[float] = None
        self._last_arduino_state: Optional[dict[str, Any]] = None
        self._fault_reason: Optional[str] = None
        self._events: list[GateEvent] = []
        self._current_pos: dict[str, float] = {"X": 20.0, "Y": 20.0, "Z": 120.0}
        self._record("init", GateState.DISCONNECTED, "Deterministic Hardware Safety Gate initialized.")

    @property
    def state(self) -> GateState:
        with self._lock:
            return self._state

    @property
    def fault_reason(self) -> Optional[str]:
        with self._lock:
            return self._fault_reason

    @property
    def limits(self) -> CoordinateLimits:
        return self._limits

    def enter_read_only(self) -> None:
        with self._lock:
            self._transition({GateState.DISCONNECTED}, GateState.READ_ONLY, "enter_read_only", "Read-only session active.")

    def run_preflight(self, *, mk4s_ready: bool, arduino_ready: bool, operator_confirmed: bool) -> bool:
        with self._lock:
            if self._state not in (GateState.READ_ONLY, GateState.READY):
                raise RuntimeError(f"Preflight invalid from {self._state.value}")
            self._set_state(GateState.PREFLIGHT, "start_preflight", "Validating hardware telemetry & interlocks.")
            if not mk4s_ready:
                self._latch_fault("Preflight rejected: Prusa MK4S not ready.")
                return False
            if not arduino_ready:
                self._latch_fault("Preflight rejected: Arduino Mega probe controller not ready.")
                return False
            if not operator_confirmed:
                self._latch_fault("Preflight rejected: Operator confirmation missing.")
                return False
            self._set_state(GateState.READY, "preflight_passed", "All preflight safety checks passed.")
            return True

    def arm_motion(self, *, now_monotonic: float) -> None:
        with self._lock:
            self._verify_arduino_freshness(now_monotonic)
            self._transition({GateState.READY}, GateState.ARMED, "arm_motion", "System armed for verified motion.")

    def record_arduino_feedback(
        self,
        payload: dict[str, Any],
        now_monotonic: float,
    ) -> None:
        with self._lock:
            if not isinstance(payload, dict):
                self._latch_fault("Malformed Arduino feedback received.")
                return
            if payload.get("identity") != "SPM_PROBE_MEGA2560":
                self._latch_fault(f"Unexpected probe identity: {payload.get('identity')}")
                return
            self._last_arduino_feedback_monotonic = now_monotonic
            self._last_arduino_state = payload

    def check_watchdog(self, now_monotonic: float) -> None:
        with self._lock:
            if self._state in (GateState.ARMED, GateState.MOTION_AUTHORIZED):
                self._verify_arduino_freshness(now_monotonic)

    def authorize_linear_move(
        self,
        *,
        x: Optional[float] = None,
        y: Optional[float] = None,
        z: Optional[float] = None,
        feedrate_mm_s: float,
        now_monotonic: float,
    ) -> str:
        with self._lock:
            self._verify_arduino_freshness(now_monotonic)

            if self._state not in (GateState.ARMED, GateState.MOTION_AUTHORIZED):
                raise PermissionError(f"Motion denied: Gate is in state {self._state.value}, must be ARMED.")

            target_x = self._current_pos["X"] if x is None else float(x)
            target_y = self._current_pos["Y"] if y is None else float(y)
            target_z = self._current_pos["Z"] if z is None else float(z)

            # Validate coordinate bounds
            if not (self._limits.x_min_mm <= target_x <= self._limits.x_max_mm):
                self._latch_fault(f"X target {target_x:.2f} outside safe limit [{self._limits.x_min_mm}, {self._limits.x_max_mm}]")
                raise ValueError(f"X coordinate {target_x} out of safe bounds.")

            if not (self._limits.y_min_mm <= target_y <= self._limits.y_max_mm):
                self._latch_fault(f"Y target {target_y:.2f} outside safe limit [{self._limits.y_min_mm}, {self._limits.y_max_mm}]")
                raise ValueError(f"Y coordinate {target_y} out of safe bounds.")

            if not (self._limits.z_min_floor_mm <= target_z <= self._limits.z_max_mm):
                self._latch_fault(f"Z target {target_z:.2f} below safe floor [{self._limits.z_min_floor_mm}, {self._limits.z_max_mm}]")
                raise ValueError(f"Z coordinate {target_z} below hard safe floor.")

            # Validate feedrates
            is_z_move = z is not None and abs(target_z - self._current_pos["Z"]) > 1e-4
            max_feed = self._limits.max_feedrate_z_mm_s if is_z_move else self._limits.max_feedrate_xy_mm_s
            if feedrate_mm_s <= 0 or feedrate_mm_s > max_feed:
                self._latch_fault(f"Invalid feedrate {feedrate_mm_s} mm/s (max {max_feed})")
                raise ValueError(f"Feedrate {feedrate_mm_s} violates velocity bounds.")

            self._current_pos["X"] = target_x
            self._current_pos["Y"] = target_y
            self._current_pos["Z"] = target_z

            self._set_state(GateState.MOTION_AUTHORIZED, "authorize_move", f"Move approved: X{target_x} Y{target_y} Z{target_z} F{feedrate_mm_s}")
            feed_mm_min = feedrate_mm_s * 60.0
            return f"G1 X{target_x:.3f} Y{target_y:.3f} Z{target_z:.3f} F{feed_mm_min:.1f}"

    def filter_raw_gcode(self, gcode: str) -> None:
        """Reject unverified or prohibited G-code."""
        normalized = gcode.strip().upper()
        for forbidden in self.FORBIDDEN_GCODE:
            if normalized.startswith(forbidden):
                self._latch_fault(f"Prohibited G-code command blocked: {gcode}")
                raise PermissionError(f"Prohibited command: {gcode}")

    def emergency_stop(self, reason: str = "Operator emergency stop triggered.") -> None:
        with self._lock:
            self._fault_reason = reason
            self._set_state(GateState.E_STOP, "e_stop", reason)

    def acknowledge_fault(self, *, operator_id: str) -> None:
        with self._lock:
            if self._state not in (GateState.FAULT, GateState.E_STOP):
                raise RuntimeError(f"Cannot acknowledge fault from {self._state.value}")
            self._fault_reason = None
            self._set_state(
                GateState.DISCONNECTED,
                "fault_acknowledged",
                f"Fault acknowledged by operator '{operator_id}'. New preflight required.",
            )

    def _verify_arduino_freshness(self, now_monotonic: float) -> None:
        if self._last_arduino_feedback_monotonic is None:
            self._latch_fault("No Arduino feedback received prior to motion request.")
            raise ConnectionError("Arduino telemetry missing.")

        age = now_monotonic - self._last_arduino_feedback_monotonic
        if age > self._feedback_deadline_s:
            self._latch_fault(f"Arduino feedback stale (age={age*1000:.1f}ms, deadline={self._feedback_deadline_s*1000:.1f}ms).")
            raise TimeoutError("Arduino watchdog triggered: feedback stale.")

    def _latch_fault(self, reason: str) -> None:
        if self._state == GateState.E_STOP:
            return
        self._fault_reason = reason
        self._set_state(GateState.FAULT, "fault_latched", reason)

    def _transition(self, allowed_from: set[GateState], target: GateState, event: str, detail: str) -> None:
        if self._state not in allowed_from:
            allowed = ", ".join(s.value for s in allowed_from)
            raise RuntimeError(f"{event} invalid from {self._state.value}; allowed: {allowed}")
        self._set_state(target, event, detail)

    def _set_state(self, target: GateState, event: str, detail: str) -> None:
        prev = self._state
        self._state = target
        self._record(event, prev, detail)

    def _record(self, event: str, prev: GateState, detail: str) -> None:
        self._events.append(
            GateEvent(
                timestamp=datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
                event=event,
                from_state=prev,
                to_state=self._state,
                detail=detail,
            )
        )

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {
                "state": self._state.value,
                "fault_reason": self._fault_reason,
                "current_position": dict(self._current_pos),
                "limits": {
                    "x": [self._limits.x_min_mm, self._limits.x_max_mm],
                    "y": [self._limits.y_min_mm, self._limits.y_max_mm],
                    "z": [self._limits.z_min_floor_mm, self._limits.z_max_mm],
                },
                "feedback_deadline_ms": self._feedback_deadline_s * 1000.0,
                "events": [
                    {
                        "timestamp": e.timestamp,
                        "event": e.event,
                        "from_state": e.from_state.value,
                        "to_state": e.to_state.value,
                        "detail": e.detail,
                    }
                    for e in self._events[-10:]
                ],
            }


HARDWARE_SAFETY_GATE = DeterministicHardwareSafetyGate()

