"""Web-safe Z scanner control facade for Phase 2.2."""

from __future__ import annotations

import os
import re
from typing import Any

from core.system.mk4s_z_auto_approach import (
    confirmed_approach_reference,
    planned_auto_approach_commands,
    request_z_motion_stop,
    run_mk4s_z_auto_approach,
    run_mk4s_z_manual_step,
    run_mk4s_z_move_to_setpoint,
    run_mk4s_z_safe_retract,
)
from core.system.hardware_initialized_profile import load_hardware_initialized_profile
from core.web.mk4s_readonly_connection import connect_real_hardware_readonly


Z_RESOLUTION_MM = 0.0025


def _z_motion_allowed() -> bool:
    return os.getenv("SPM_WEB_ALLOW_Z_MOTION", "").strip() == "1"


def _readonly_allowed() -> bool:
    return os.getenv("SPM_WEB_ALLOW_READONLY_HARDWARE", "").strip() == "1"


def _parse_position(position: str) -> dict[str, float | None]:
    values: dict[str, float | None] = {"x": None, "y": None, "z": None, "count_z": None}
    for axis in ("X", "Y", "Z"):
        match = re.search(rf"\b{axis}:([+-]?\d+(?:\.\d+)?)", position)
        if match:
            values[axis.lower()] = float(match.group(1))
    count = re.search(r"Count\s+X:[+-]?\d+\s+Y:[+-]?\d+\s+Z:([+-]?\d+)", position)
    if count:
        values["count_z"] = float(count.group(1))
    return values


def z_reference_payload() -> dict[str, Any]:
    reference = confirmed_approach_reference()
    auto = reference["auto_step_approach_confirmed"]
    return {
        "ok": True,
        "status": "ready",
        "reference": reference,
        "surface_z_mm": float(reference["manual_near_contact_z"]),
        "safe_min_z_mm": float(reference["do_not_go_below_without_contact_detection"]),
        "start_z_mm": float(auto["start_z"]),
        "safe_retract_z_mm": float(auto["safe_retract_z"]),
        "x_mm": float(auto["x"]),
        "y_mm": float(auto["y"]),
        "feedrate": float(auto["feedrate"]),
        "z_resolution_mm": Z_RESOLUTION_MM,
        "z_resolution_um": Z_RESOLUTION_MM * 1000.0,
    }


def z_read_status(port: str | None = None) -> dict[str, Any]:
    reference = z_reference_payload()
    if not _readonly_allowed():
        return {
            **reference,
            "ok": False,
            "status": "readonly_locked",
            "message": "Current Z read is locked. Start server with SPM_WEB_ALLOW_READONLY_HARDWARE=1.",
            "position": "",
            "current": {"x": None, "y": None, "z": None, "count_z": None},
            "log_lines": ["Z read blocked: read-only hardware gate is not enabled."],
        }

    result = connect_real_hardware_readonly(port=port, settle_seconds=0.20)
    position = str(result.get("position", ""))
    current = _parse_position(position)
    z = current.get("z")
    surface = reference["surface_z_mm"]
    clearance_um = None if z is None else (z - surface) * 1000.0
    return {
        **reference,
        "ok": bool(result.get("ready")),
        "status": "read" if result.get("ready") else "not_ready",
        "message": result.get("message", "Z read complete."),
        "port": result.get("port", ""),
        "position": position,
        "current": current,
        "clearance_um": clearance_um,
        "hardware": result,
        "log_lines": list(result.get("log_lines") or []),
    }


def z_auto_preview(setpoint_distance_mm: float = 0.0, retract_after: bool = False) -> dict[str, Any]:
    commands = planned_auto_approach_commands(
        setpoint_distance_mm=setpoint_distance_mm,
        retract_after=retract_after,
    )
    result = run_mk4s_z_auto_approach(
        execute=False,
        setpoint_distance_mm=setpoint_distance_mm,
        retract_after=retract_after,
    )
    return {
        **z_reference_payload(),
        "ok": True,
        "status": "preview",
        "message": result.message,
        "final_z": result.final_z,
        "commands": commands,
        "log_lines": [result.message],
    }


def z_auto_approach(*, setpoint_distance_mm: float, retract_after: bool, confirmed: bool) -> dict[str, Any]:
    if not confirmed:
        return {
            **z_auto_preview(setpoint_distance_mm=setpoint_distance_mm, retract_after=retract_after),
            "ok": False,
            "status": "confirmation_required",
            "message": "Auto approach requires operator confirmation.",
            "log_lines": ["Z auto approach blocked: confirmation missing."],
        }
    if not _z_motion_allowed():
        return {
            **z_auto_preview(setpoint_distance_mm=setpoint_distance_mm, retract_after=retract_after),
            "ok": False,
            "status": "motion_locked",
            "message": "Real Z motion locked. Start server with SPM_WEB_ALLOW_Z_MOTION=1 to execute.",
            "log_lines": ["Z auto approach blocked: SPM_WEB_ALLOW_Z_MOTION is not enabled."],
        }
    result = run_mk4s_z_auto_approach(
        execute=True,
        setpoint_distance_mm=setpoint_distance_mm,
        retract_after=retract_after,
    )
    return {
        **z_reference_payload(),
        "ok": result.success,
        "status": "complete" if result.success else "failed",
        "message": result.message,
        "final_z": result.final_z,
        "commands": result.commands,
        "responses": result.responses,
        "log_lines": [result.message, *result.responses],
    }


def z_move_to_setpoint(*, target_z_mm: float, confirmed: bool) -> dict[str, Any]:
    preview = run_mk4s_z_move_to_setpoint(target_z_mm=target_z_mm, execute=False)
    if not confirmed:
        return {
            **z_reference_payload(),
            "ok": False,
            "status": "confirmation_required",
            "message": "Apply Target Z requires operator confirmation.",
            "command": preview.command,
            "target_z": preview.target_z,
            "log_lines": ["Apply Target Z blocked: confirmation missing."],
        }
    if not _z_motion_allowed():
        return {
            **z_reference_payload(),
            "ok": False,
            "status": "motion_locked",
            "message": "Real Z motion locked. Start server with SPM_WEB_ALLOW_Z_MOTION=1 to execute.",
            "command": preview.command,
            "target_z": preview.target_z,
            "log_lines": ["Apply Target Z blocked: SPM_WEB_ALLOW_Z_MOTION is not enabled."],
        }

    result = run_mk4s_z_move_to_setpoint(target_z_mm=target_z_mm, execute=True)
    return {
        **z_reference_payload(),
        "ok": result.success,
        "status": "complete" if result.success else "failed",
        "message": result.message,
        "command": result.command,
        "target_z": result.target_z,
        "responses": result.responses,
        "log_lines": [result.message, *result.responses],
    }


def z_manual_step(*, direction: str, step_mm: float, confirmed: bool) -> dict[str, Any]:
    if not confirmed:
        result = run_mk4s_z_manual_step(direction=direction, step_mm=step_mm, execute=False)
        return {
            **z_reference_payload(),
            "ok": False,
            "status": "confirmation_required",
            "message": "Manual Z move requires operator confirmation.",
            "command": result.command,
            "log_lines": ["Manual Z move blocked: confirmation missing."],
        }
    if not _z_motion_allowed():
        result = run_mk4s_z_manual_step(direction=direction, step_mm=step_mm, execute=False)
        return {
            **z_reference_payload(),
            "ok": False,
            "status": "motion_locked",
            "message": "Real Z motion locked. Start server with SPM_WEB_ALLOW_Z_MOTION=1 to execute.",
            "command": result.command,
            "log_lines": ["Manual Z move blocked: SPM_WEB_ALLOW_Z_MOTION is not enabled."],
        }
    result = run_mk4s_z_manual_step(direction=direction, step_mm=step_mm, execute=True)
    return {
        **z_reference_payload(),
        "ok": result.success,
        "status": "complete" if result.success else "failed",
        "message": result.message,
        "command": result.command,
        "target_z": result.target_z,
        "responses": result.responses,
        "log_lines": [result.message, *result.responses],
    }


def z_retract(*, confirmed: bool) -> dict[str, Any]:
    if not confirmed:
        result = run_mk4s_z_safe_retract(execute=False)
        return {
            **z_reference_payload(),
            "ok": False,
            "status": "confirmation_required",
            "message": "Z retract requires operator confirmation.",
            "command": result.command,
            "target_z": result.target_z,
            "log_lines": ["Z retract blocked: confirmation missing."],
        }
    if not _z_motion_allowed():
        result = run_mk4s_z_safe_retract(execute=False)
        return {
            **z_reference_payload(),
            "ok": False,
            "status": "motion_locked",
            "message": "Real Z motion locked. Start server with SPM_WEB_ALLOW_Z_MOTION=1 to execute.",
            "command": result.command,
            "target_z": result.target_z,
            "log_lines": ["Z retract blocked: SPM_WEB_ALLOW_Z_MOTION is not enabled."],
        }
    result = run_mk4s_z_safe_retract(execute=True)
    return {
        **z_reference_payload(),
        "ok": result.success,
        "status": "complete" if result.success else "failed",
        "message": result.message,
        "command": result.command,
        "target_z": result.target_z,
        "responses": result.responses,
        "log_lines": [result.message, *result.responses],
    }


def z_stop_now() -> dict[str, Any]:
    request_z_motion_stop()
    return {
        **z_reference_payload(),
        "ok": True,
        "status": "stop_requested",
        "message": "Z stop requested. Active Z sequence will stop at the next verified command boundary.",
        "log_lines": ["Z stop requested. Software stop flag set; no firmware quick-stop command was sent."],
    }


def measurement_limits_payload() -> dict[str, Any]:
    profile = load_hardware_initialized_profile()
    limits = profile["hardware_initialized_profile"]["motion_limits"]
    from core.web.mk4s_motion_limits import motion_limits_payload

    mk4s = motion_limits_payload()
    return {
        "ok": True,
        "status": "ready",
        "limits": {
            "x_min": float(limits["x_min"]),
            "x_max": float(limits["x_max"]),
            "y_min": float(limits["y_min"]),
            "y_max": float(limits["y_max"]),
            "z_min": float(limits["z_min"]),
            "z_max": float(limits["z_max"]),
        },
        "scanner": {
            "recommended_x_min": mk4s["x_safe_min_mm"],
            "recommended_x_max": mk4s["x_safe_max_mm"],
            "recommended_y_min": mk4s["y_safe_min_mm"],
            "recommended_y_max": mk4s["y_safe_max_mm"],
            "min_xy_step_mm": 0.01,
            "z_step_mm": Z_RESOLUTION_MM,
            "default_scan_speed_mm_s": mk4s["recommended_scan_speed_default_mm_s"],
            "recommended_scan_speed_min_mm_s": mk4s["recommended_scan_speed_min_mm_s"],
            "recommended_scan_speed_max_mm_s": mk4s["recommended_scan_speed_max_mm_s"],
            "safe_center_x_mm": mk4s["safe_center_x_mm"],
            "safe_center_y_mm": mk4s["safe_center_y_mm"],
            "safe_parking_z_mm": mk4s["safe_parking_z_mm"],
        },
        "machine": mk4s,
        "log_lines": ["Measurement limits loaded from initialized hardware profile."],
    }
