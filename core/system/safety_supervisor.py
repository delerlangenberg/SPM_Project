"""Deterministic, simulation-only lifecycle authority for Phase 2.

No method in this module opens a serial port or emits a hardware command.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from threading import RLock


class SafetyState(str, Enum):
    DISCONNECTED = "DISCONNECTED"
    READ_ONLY = "READ_ONLY"
    READY = "READY"
    ARMED = "ARMED"
    ACQUIRING = "ACQUIRING"
    RETRACTING = "RETRACTING"
    FAULT = "FAULT"
    E_STOP = "E_STOP"


@dataclass(frozen=True)
class SafetyEvent:
    timestamp: str
    event: str
    from_state: SafetyState
    to_state: SafetyState
    detail: str


class SafetySupervisor:
    """Owns allowed Phase 2 simulation lifecycle transitions."""

    phase = "2"
    real_motion_enabled = False

    def __init__(self) -> None:
        self._lock = RLock()
        self._state = SafetyState.DISCONNECTED
        self._fault_reason: str | None = None
        self._events: list[SafetyEvent] = []
        self._record("initialized", SafetyState.DISCONNECTED, "Simulation-only safety kernel initialized.")

    @property
    def state(self) -> SafetyState:
        with self._lock:
            return self._state

    def enter_read_only(self) -> None:
        self._transition({SafetyState.DISCONNECTED}, SafetyState.READ_ONLY, "enter_read_only", "Read-only session opened.")

    def complete_preflight(self, *, passed: bool) -> None:
        if not passed:
            self.fault("Preflight failed.")
            return
        self._transition({SafetyState.READ_ONLY}, SafetyState.READY, "preflight_passed", "Simulation preflight passed.")

    def arm_simulation(self) -> None:
        self._transition({SafetyState.READY}, SafetyState.ARMED, "arm_simulation", "Simulation acquisition armed.")

    def start_simulation_acquisition(self) -> None:
        self._transition({SafetyState.ARMED}, SafetyState.ACQUIRING, "start_simulation_acquisition", "Simulation acquisition started.")

    def begin_retract(self) -> None:
        self._transition(
            {SafetyState.READY, SafetyState.ARMED, SafetyState.ACQUIRING, SafetyState.FAULT},
            SafetyState.RETRACTING,
            "begin_retract",
            "Simulation retract started.",
        )

    def complete_retract(self) -> None:
        self._transition({SafetyState.RETRACTING}, SafetyState.READY, "retract_complete", "Simulation retract complete.")

    def disconnect(self) -> None:
        self._transition(
            {SafetyState.DISCONNECTED, SafetyState.READ_ONLY, SafetyState.READY},
            SafetyState.DISCONNECTED,
            "disconnect",
            "Session disconnected.",
        )

    def fault(self, reason: str) -> None:
        with self._lock:
            if self._state is SafetyState.E_STOP:
                raise RuntimeError("Cannot replace an emergency-stop state with a fault.")
            self._fault_reason = reason
            self._set_state(SafetyState.FAULT, "fault", reason)

    def emergency_stop(self, reason: str = "Emergency stop requested.") -> None:
        with self._lock:
            self._fault_reason = reason
            self._set_state(SafetyState.E_STOP, "emergency_stop", reason)

    def acknowledge_emergency_stop(self) -> None:
        self._transition(
            {SafetyState.E_STOP},
            SafetyState.DISCONNECTED,
            "emergency_stop_acknowledged",
            "Emergency stop acknowledged; a new read-only session is required.",
        )
        with self._lock:
            self._fault_reason = None

    def authorize_real_motion(self) -> None:
        raise PermissionError("Real motion is permanently disabled during Phase 2.")

    def real_motion_permitted(self) -> bool:
        """Return the sole Phase 2 decision for any physical-motion request."""
        return False

    def snapshot(self) -> dict[str, object]:
        with self._lock:
            return {
                "phase": self.phase,
                "state": self._state.value,
                "real_motion_enabled": self.real_motion_enabled,
                "serial_opened": False,
                "gcode_sent": False,
                "fault_reason": self._fault_reason,
                "event_count": len(self._events),
                "recent_events": [
                    {
                        "timestamp": event.timestamp,
                        "event": event.event,
                        "from_state": event.from_state.value,
                        "to_state": event.to_state.value,
                        "detail": event.detail,
                    }
                    for event in self._events[-10:]
                ],
            }

    def _transition(self, allowed_from: set[SafetyState], target: SafetyState, event: str, detail: str) -> None:
        with self._lock:
            if self._state not in allowed_from:
                allowed = ", ".join(state.value for state in sorted(allowed_from, key=lambda item: item.value))
                raise RuntimeError(f"{event} is invalid from {self._state.value}; allowed states: {allowed}.")
            self._set_state(target, event, detail)

    def _set_state(self, target: SafetyState, event: str, detail: str) -> None:
        previous = self._state
        self._state = target
        self._record(event, previous, detail)

    def _record(self, event: str, previous: SafetyState, detail: str) -> None:
        self._events.append(
            SafetyEvent(
                timestamp=datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
                event=event,
                from_state=previous,
                to_state=self._state,
                detail=detail,
            )
        )


SAFETY_SUPERVISOR = SafetySupervisor()