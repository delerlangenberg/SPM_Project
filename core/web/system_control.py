"""Safe main-system control for the web operator console.

Phase 2.1J separates simulation/dry-run, locked hardware-read-only,
and blocked real-motion modes.

Safety:
- default is dry-run
- hardware read-only is visible but locked unless an explicit later gate is enabled
- real motion is blocked
- no serial is opened here
- no G-code is sent here
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from typing import Any

from core.web.hardware_status_adapter import hardware_information_status, validate_readonly_plan


@dataclass
class SystemState:
    powered: bool = False
    mode: str = "dry_run"
    last_action: str = "not_started"
    real_motion_enabled: bool = False
    dry_run_plan: list[str] = field(default_factory=list)


STATE = SystemState()


READ_ONLY_STARTUP_PLAN = [
    "M115 ; firmware/version read-only check",
    "M119 ; endstop/probe state read-only check",
    "M105 ; temperature read-only check",
    "M114 ; position read-only check",
]


def _real_motion_allowed() -> bool:
    return os.getenv("SPM_WEB_ALLOW_REAL_MOTION", "").strip() in {"1", "true", "TRUE", "yes", "YES"}


def _readonly_hardware_allowed() -> bool:
    return os.getenv("SPM_WEB_ALLOW_READONLY_HARDWARE", "").strip() in {"1", "true", "TRUE", "yes", "YES"}


def system_status() -> dict[str, Any]:
    """Return current safe system status."""
    STATE.real_motion_enabled = _real_motion_allowed()
    hardware_info = hardware_information_status()

    return {
        "status": "ok",
        "powered": STATE.powered,
        "mode": STATE.mode,
        "last_action": STATE.last_action,
        "real_motion_enabled": STATE.real_motion_enabled,
        "readonly_hardware_enabled": _readonly_hardware_allowed(),
        "simulation_status": {
            "available": True,
            "mode": "web_simulation_dry_run",
            "powered": STATE.powered,
            "scan_model": "constant_distance_z_feedback_raster",
        },
        "hardware_information_status": hardware_info,
        "hardware_information_plan_valid": validate_readonly_plan(hardware_info),
        "safety": {
            "default_mode": "dry_run",
            "motion_allowed_this_phase": False,
            "real_hardware_requires_later_phase": True,
            "serial_opened": False,
            "gcode_sent": False,
        },
        "dry_run_plan": list(STATE.dry_run_plan),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    }


def system_on(mode: str = "dry_run") -> dict[str, Any]:
    """Start the main system in dry-run or locked hardware-read-only mode."""
    requested_mode = (mode or "dry_run").strip().lower()

    if requested_mode not in {"dry_run", "hardware_readonly", "hardware", "hardware_motion"}:
        requested_mode = "dry_run"

    readonly_hardware_enabled = _readonly_hardware_allowed()

    if requested_mode in {"hardware", "hardware_motion"}:
        STATE.powered = False
        STATE.mode = "dry_run"
        STATE.last_action = "hardware_motion_start_blocked"
        STATE.dry_run_plan = []

        return {
            **system_status(),
            "status": "blocked",
            "message": "Hardware motion start is blocked. Motion is not allowed from the web console in this phase.",
        }

    if requested_mode == "hardware_readonly" and not readonly_hardware_enabled:
        STATE.powered = False
        STATE.mode = "hardware_readonly_locked"
        STATE.last_action = "hardware_readonly_start_blocked_gate_disabled"
        STATE.dry_run_plan = []

        return {
            **system_status(),
            "status": "blocked",
            "message": "Hardware read-only mode is visible but locked. Enable only in a later dedicated read-only serial phase.",
        }

    if requested_mode == "hardware_readonly" and readonly_hardware_enabled:
        STATE.powered = True
        STATE.mode = "hardware_readonly_gate_enabled_no_serial_yet"
        STATE.last_action = "hardware_readonly_gate_enabled"
        STATE.dry_run_plan = []

        return {
            **system_status(),
            "message": "Hardware read-only gate is enabled, but this phase still does not open serial or send commands.",
        }

    STATE.powered = True
    STATE.mode = "dry_run"
    STATE.last_action = "system_on_dry_run"
    STATE.dry_run_plan = list(READ_ONLY_STARTUP_PLAN)

    return {
        **system_status(),
        "message": "System ON completed in dry-run mode. No hardware command was sent.",
    }


def system_off() -> dict[str, Any]:
    """Stop the main system shell safely."""
    STATE.powered = False
    STATE.last_action = "system_off"
    STATE.dry_run_plan = []

    return {
        **system_status(),
        "message": "System OFF completed. Dry-run gateway is no longer active.",
    }


def system_close() -> dict[str, Any]:
    """Close/park shell safely.

    Real park motion is not executed in this phase.
    """
    STATE.powered = False
    STATE.last_action = "system_close_requested"
    STATE.dry_run_plan = []

    return {
        **system_status(),
        "message": "Close workflow completed in dry-run. Real park/shutdown will be connected later.",
    }


def dry_run_startup_plan() -> dict[str, Any]:
    """Return the startup plan that will be used before real hardware is connected."""
    STATE.dry_run_plan = list(READ_ONLY_STARTUP_PLAN)

    return {
        "status": "ok",
        "mode": "dry_run",
        "execution_allowed": False,
        "gcode_sent": False,
        "purpose": "Show the read-only startup checks planned for later hardware integration.",
        "plan": list(READ_ONLY_STARTUP_PLAN),
    }
