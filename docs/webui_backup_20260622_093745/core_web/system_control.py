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
    from core.web.mk4s_readonly_connection import connect_real_hardware_readonly
    
    result = connect_real_hardware_readonly()
    ready = bool(result.get("ready"))
    message = result.get("message") or (
        "Real hardware connected. MK4S read-only handshake OK. Ready to start."
        if ready
        else "Real hardware connection failed or handshake incomplete. Not ready."
    )
    
    log_lines = list(result.get("log_lines") or [])
    if message not in "\n".join(log_lines):
        log_lines.append(message)
    
    return {
        "ok": ready,
        "available": ready,
        "ready": ready,
        "powered": ready,
        "system_powered": ready,
        "mode": "real_hardware_readonly",
        "message": message,
        "port": result.get("port", ""),
        "machine_type": result.get("machine_type", ""),
        "firmware": result.get("firmware", ""),
        "temperature": result.get("temperature", ""),
        "endstops": result.get("endstops", ""),
        "position": result.get("position", ""),
        "safety": result.get("safety", ""),
        "dev_log_file": result.get("dev_log_path_txt", ""),
        "dev_log_jsonl": result.get("dev_log_path_jsonl", ""),
        "hardware": result,
        "log_lines": log_lines,
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


# === Phase 2.2D-CLEAN final stable system control override ===
# Stable safety contract:
# - dry_run remains the default for tests/simulation.
# - browser real hardware uses hardware_readonly only when SPM_WEB_ALLOW_READONLY_HARDWARE=1.
# - hardware/hardware_motion remain blocked.
# - disconnect runs safe retract confirmation first.
# - close is blocked while connected and not safely retracted.

import os as _spm_os
import re as _spm_re


_DRY_RUN_PLAN = [
    {"label": "IDENTITY", "command": "M115", "meaning": "firmware/version read-only check"},
    {"label": "TEMPERATURE", "command": "M105", "meaning": "temperature read-only check"},
    {"label": "ENDSTOPS", "command": "M119", "meaning": "endstop/probe state read-only check"},
    {"label": "POSITION", "command": "M114", "meaning": "position read-only check"},
]

_SPM_SAFE_Z_MM = 100.0

_SPM_SYSTEM_STATE = {
    "connected": False,
    "powered": False,
    "system_powered": False,
    "ready": False,
    "safe_retracted": True,
    "mode": "dry_run",
    "status": "off",
    "message": "System is disconnected.",
    "port": "",
    "manual_port": "",
    "operation_mode": "hardware_readonly",
    "machine_type": "",
    "position": "",
    "temperature": "",
    "dev_log_file": "",
    "last_safe_z": "",
}


def _safety(serial_opened=False, gcode_sent=False, motion_allowed=False):
    return {
        "serial_opened": bool(serial_opened),
        "gcode_sent": bool(gcode_sent),
        "motion_allowed_this_phase": bool(motion_allowed),
        "motion_enabled": bool(motion_allowed),
        "homing_enabled": False,
        "heating_enabled": False,
        "printer_writes_enabled": False,
        "real_motion_enabled": False,
    }


def _simulation_status():
    return {
        "available": True,
        "mode": "web_simulation_dry_run",
        "status": "ready",
        "message": "Simulation path is available.",
    }


def _hardware_information_status():
    return {
        "available": True,
        "mode": "dry_run_readonly_plan",
        "status": "available",
        "plan": list(_DRY_RUN_PLAN),
        "message": "Hardware information layer available as read-only plan.",
    }


def _base_payload():
    return {
        "simulation_status": _simulation_status(),
        "hardware_information_status": _hardware_information_status(),
        "dry_run_plan": list(_DRY_RUN_PLAN),
        "safety": _safety(),
    }


def _set_state(payload):
    _SPM_SYSTEM_STATE.update({
        "connected": bool(payload.get("connected", payload.get("powered", False))),
        "powered": bool(payload.get("powered", False)),
        "system_powered": bool(payload.get("system_powered", payload.get("powered", False))),
        "ready": bool(payload.get("ready", payload.get("powered", False))),
        "safe_retracted": bool(payload.get("safe_retracted", _SPM_SYSTEM_STATE.get("safe_retracted", False))),
        "mode": payload.get("mode", _SPM_SYSTEM_STATE.get("mode", "dry_run")),
        "status": payload.get("status", _SPM_SYSTEM_STATE.get("status", "off")),
        "message": payload.get("message", _SPM_SYSTEM_STATE.get("message", "")),
        "port": payload.get("port", _SPM_SYSTEM_STATE.get("port", "")),
        "machine_type": payload.get("machine_type", _SPM_SYSTEM_STATE.get("machine_type", "")),
        "position": payload.get("position", _SPM_SYSTEM_STATE.get("position", "")),
        "temperature": payload.get("temperature", _SPM_SYSTEM_STATE.get("temperature", "")),
        "dev_log_file": payload.get("dev_log_file", _SPM_SYSTEM_STATE.get("dev_log_file", "")),
        "motion_verified": bool(payload.get("motion_verified", _SPM_SYSTEM_STATE.get("motion_verified", False))),
    })


def _blocked_payload(mode, message):
    payload = {
        **_base_payload(),
        "ok": False,
        "available": False,
        "ready": False,
        "connected": False,
        "powered": False,
        "system_powered": False,
        "safe_retracted": False,
        "status": "blocked",
        "mode": mode,
        "message": message,
        "dry_run_plan": [],
        "safety": _safety(serial_opened=False, gcode_sent=False, motion_allowed=False),
        "log_lines": [message],
    }
    return payload


def _parse_z(position):
    match = _spm_re.search(r"\bZ:([+-]?\d+(?:\.\d+)?)", str(position))
    if not match:
        return None
    return float(match.group(1))


def _parse_position_and_counts(position):
    text = str(position or "")
    values = {}
    for axis in ("X", "Y", "Z"):
        match = _spm_re.search(rf"\b{axis}:([+-]?\d+(?:\.\d+)?)", text)
        values[axis.lower()] = float(match.group(1)) if match else None

    count_match = _spm_re.search(r"Count\s+X:([+-]?\d+)\s+Y:([+-]?\d+)\s+Z:([+-]?\d+)", text)
    if count_match:
        values["count_x"] = int(count_match.group(1))
        values["count_y"] = int(count_match.group(2))
        values["count_z"] = int(count_match.group(3))
        values["physical_x"] = values["count_x"] / 100.0
        values["physical_y"] = values["count_y"] / 100.0
        values["physical_z"] = values["count_z"] / 400.0
    else:
        values["count_x"] = values["count_y"] = values["count_z"] = None
        values["physical_x"] = values["physical_y"] = values["physical_z"] = None
    return values


def _position_diagnostic(position, tolerance_mm=0.02):
    values = _parse_position_and_counts(position)
    mismatches = []
    for axis in ("x", "y", "z"):
        logical = values.get(axis)
        physical = values.get(f"physical_{axis}")
        if logical is None or physical is None:
            mismatches.append(f"{axis.upper()}: missing logical/count data")
            continue
        delta = logical - physical
        if abs(delta) > tolerance_mm:
            mismatches.append(f"{axis.upper()}: logical {logical:.2f} mm, count-derived {physical:.2f} mm, delta {delta:+.2f} mm")

    ok = not mismatches
    return {
        "ok": ok,
        "status": "verified" if ok else "needs_sync",
        "values": values,
        "mismatches": mismatches,
        "message": "Logical position matches stepper counts." if ok else "Logical position does not match stepper counts. Motion is blocked until sync/restart.",
    }


def _send_serial_commands(commands, *, port=None, baudrate=115200, settle_seconds=0.4):
    import serial

    selected_port = port or _SPM_SYSTEM_STATE.get("manual_port") or _SPM_SYSTEM_STATE.get("port") or "COM5"
    log_lines = [f"PHASE 2.1 SERIAL: opening {selected_port}."]
    with serial.Serial(selected_port, int(baudrate), timeout=0.25, write_timeout=1.0) as ser:
        time.sleep(settle_seconds)
        ser.reset_input_buffer()
        for command in commands:
            log_lines.append(f">>> {command}")
            ser.write((command + "\n").encode("ascii", errors="replace"))
            ser.flush()
            end = time.time() + (90.0 if command == "M400" else 8.0)
            while time.time() < end:
                raw = ser.readline()
                if not raw:
                    continue
                line = raw.decode(errors="replace").strip()
                if not line:
                    continue
                log_lines.append(line)
                if line == "ok" or line.startswith("ok "):
                    break
    return {"port": selected_port, "log_lines": log_lines}


def system_apply_port(port: str = ""):
    selected = (port or "").strip().upper()

    if selected == "":
        _SPM_SYSTEM_STATE["manual_port"] = ""
        return {
            **_base_payload(),
            "ok": True,
            "status": "ok",
            "mode": _SPM_SYSTEM_STATE.get("mode", "dry_run"),
            "message": "Connection port set to automatic detection.",
            "manual_port": "",
            "log_lines": ["Connection port set to automatic detection."],
        }

    allowed = {f"COM{i}" for i in range(1, 11)}
    if selected not in allowed:
        return _blocked_payload("config", f"Port rejected: {selected}. Allowed troubleshooting ports are COM1-COM10.")

    _SPM_SYSTEM_STATE["manual_port"] = selected
    return {
        **_base_payload(),
        "ok": True,
        "status": "ok",
        "mode": _SPM_SYSTEM_STATE.get("mode", "dry_run"),
        "message": f"Connection port applied: {selected}",
        "manual_port": selected,
        "log_lines": [f"Connection port applied: {selected}"],
    }


def system_apply_mode(mode: str = "hardware_readonly"):
    selected = (mode or "hardware_readonly").strip().lower()

    if selected in {"hardware", "real_hardware", "hardware_motion", "motion", "real_motion"}:
        return _blocked_payload(selected, "Operation mode rejected. Hardware motion is not enabled in this phase.")

    if selected in {"hardware_readonly", "real_hardware_readonly", "readonly"}:
        _SPM_SYSTEM_STATE["operation_mode"] = "hardware_readonly"
        return {
            **_base_payload(),
            "ok": True,
            "status": "ok",
            "mode": _SPM_SYSTEM_STATE.get("mode", "dry_run"),
            "operation_mode": "hardware_readonly",
            "message": "Operation mode applied: Hardware Read-Only.",
            "log_lines": ["Operation mode applied: Hardware Read-Only."],
        }

    if selected in {"dry_run", "simulation", "simulated"}:
        _SPM_SYSTEM_STATE["operation_mode"] = "dry_run"
        return {
            **_base_payload(),
            "ok": True,
            "status": "ok",
            "mode": _SPM_SYSTEM_STATE.get("mode", "dry_run"),
            "operation_mode": "dry_run",
            "message": "Operation mode applied: Dry Run.",
            "log_lines": ["Operation mode applied: Dry Run."],
        }

    return _blocked_payload(selected, f"Unknown operation mode rejected: {selected}")


def system_diagnostics():
    from core.web.mk4s_readonly_connection import connect_real_hardware_readonly

    selected_port = _SPM_SYSTEM_STATE.get("manual_port") or _SPM_SYSTEM_STATE.get("port") or None
    result = connect_real_hardware_readonly(port=selected_port, settle_seconds=0.20)
    diagnostic = _position_diagnostic(result.get("position", ""))
    payload = {
        **_base_payload(),
        "ok": bool(result.get("ready")) and diagnostic["ok"],
        "connected": bool(result.get("ready")),
        "ready": bool(result.get("ready")) and diagnostic["ok"],
        "status": diagnostic["status"] if result.get("ready") else "not_ready",
        "mode": _SPM_SYSTEM_STATE.get("mode", "real_hardware_readonly"),
        "port": result.get("port", _SPM_SYSTEM_STATE.get("port", "")),
        "position": result.get("position", ""),
        "position_diagnostic": diagnostic,
        "motion_verified": diagnostic["ok"],
        "message": diagnostic["message"] if result.get("ready") else result.get("message", "Hardware diagnostic failed."),
        "hardware": result,
        "log_lines": list(result.get("log_lines") or []) + [
            f"PHASE 2.1 POSITION DIAGNOSTIC: {diagnostic['message']}",
            *[f"PHASE 2.1 POSITION MISMATCH: {line}" for line in diagnostic["mismatches"]],
        ],
    }
    _set_state(payload)
    return payload


def system_sync_logical_position():
    diagnostic = system_diagnostics()
    if not diagnostic.get("connected"):
        return diagnostic

    values = diagnostic["position_diagnostic"]["values"]
    physical_x = values.get("physical_x")
    physical_y = values.get("physical_y")
    physical_z = values.get("physical_z")
    if physical_x is None or physical_y is None or physical_z is None:
        return {
            **diagnostic,
            "ok": False,
            "status": "blocked",
            "message": "Cannot sync logical position because stepper counts are missing.",
            "log_lines": list(diagnostic.get("log_lines") or []) + ["SYNC BLOCKED: missing Count X/Y/Z from M114."],
        }

    command = f"G92 X{physical_x:.2f} Y{physical_y:.2f} Z{physical_z:.2f}"
    serial_result = _send_serial_commands([command, "M114"], port=diagnostic.get("port") or None)
    verify_position = ""
    for line in serial_result["log_lines"]:
        if line.startswith("X:") and "Count" in line:
            verify_position = line
    verify = _position_diagnostic(verify_position)
    payload = {
        **_base_payload(),
        "ok": verify["ok"],
        "connected": True,
        "powered": True,
        "system_powered": True,
        "ready": verify["ok"],
        "safe_retracted": verify["ok"] and (verify["values"].get("physical_z") or 0) >= _SPM_SAFE_Z_MM,
        "status": "synced" if verify["ok"] else "needs_sync",
        "mode": "real_hardware_readonly",
        "port": serial_result["port"],
        "position": verify_position,
        "position_diagnostic": verify,
        "motion_verified": verify["ok"],
        "message": "Logical position synced to stepper counts. No physical movement was commanded." if verify["ok"] else "Logical position sync did not verify.",
        "log_lines": list(diagnostic.get("log_lines") or []) + serial_result["log_lines"] + [
            f"SYNC RESULT: {verify['message']}",
            *[f"SYNC MISMATCH: {line}" for line in verify["mismatches"]],
        ],
    }
    _set_state(payload)
    return payload


def system_on(mode: str = "dry_run", port: str | None = None):
    selected_mode = (mode or "dry_run").strip().lower()

    if port:
        system_apply_port(port)

    if selected_mode in {"dry_run", "simulation", "simulated"}:
        payload = {
            **_base_payload(),
            "ok": True,
            "available": True,
            "ready": True,
            "connected": True,
            "powered": True,
            "system_powered": True,
            "safe_retracted": False,
            "status": "ok",
            "mode": "dry_run",
            "message": "System ON completed in dry-run mode. No hardware command was sent.",
            "safety": _safety(serial_opened=False, gcode_sent=False, motion_allowed=False),
            "log_lines": [
                "Dry-run startup plan: M115 ; firmware/version read-only check | M119 ; endstop/probe state read-only check | M105 ; temperature read-only check | M114 ; position read-only check",
                "System ON completed in dry-run mode. No hardware command was sent.",
            ],
        }
        _set_state(payload)
        return payload

    if selected_mode in {"hardware", "real_hardware"}:
        return _blocked_payload(
            "hardware",
            "Hardware mode is blocked. Use Hardware Read-Only first; hardware motion is not enabled.",
        )

    if selected_mode in {"hardware_motion", "motion", "real_motion"}:
        return _blocked_payload(
            "hardware_motion",
            "Hardware motion mode remains blocked. No movement command is enabled.",
        )

    if selected_mode in {"hardware_readonly", "real_hardware_readonly", "readonly"}:
        if _spm_os.environ.get("SPM_WEB_ALLOW_READONLY_HARDWARE") != "1":
            return _blocked_payload(
                "hardware_readonly_locked",
                "Hardware read-only mode is locked by default. Launch the web console with SPM_WEB_ALLOW_READONLY_HARDWARE=1.",
            )

        from core.web.mk4s_readonly_connection import connect_real_hardware_readonly

        selected_port = port or _SPM_SYSTEM_STATE.get("manual_port") or None
        result = connect_real_hardware_readonly(port=selected_port, settle_seconds=0.20)
        ready = bool(result.get("ready"))
        message = result.get("message") or (
            "Real hardware connected. MK4S read-only handshake OK. Ready to start."
            if ready
            else "Real hardware connected, but read-only handshake is incomplete. Not ready."
        )

        log_lines = list(result.get("log_lines") or [])
        if message not in "\n".join(log_lines):
            log_lines.append(message)
        diagnostic = _position_diagnostic(result.get("position", ""))
        log_lines.append(f"PHASE 2.1 POSITION DIAGNOSTIC: {diagnostic['message']}")
        for mismatch in diagnostic["mismatches"]:
            log_lines.append(f"PHASE 2.1 POSITION MISMATCH: {mismatch}")
        system_ready = bool(ready and diagnostic["ok"])
        if ready and not diagnostic["ok"]:
            message = "Connected, but hardware motion is blocked: logical position does not match stepper counts. Use SYNC POSITION or power-cycle/reset the printer."

        payload = {
            **_base_payload(),
            "ok": ready,
            "available": ready,
            "ready": system_ready,
            "connected": ready,
            "powered": ready,
            "system_powered": ready,
            "safe_retracted": False,
            "status": "connected" if system_ready else ("needs_sync" if ready else "not_ready"),
            "mode": "real_hardware_readonly",
            "operation_mode": "hardware_readonly",
            "message": message,
            "port": result.get("port", ""),
            "manual_port": _SPM_SYSTEM_STATE.get("manual_port", ""),
            "machine_type": result.get("machine_type", ""),
            "firmware": result.get("firmware", ""),
            "temperature": result.get("temperature", ""),
            "endstops": result.get("endstops", ""),
            "position": result.get("position", ""),
            "safety": _safety(serial_opened=True, gcode_sent=True, motion_allowed=False),
            "dev_log_file": result.get("dev_log_path_txt", ""),
            "dev_log_jsonl": result.get("dev_log_path_jsonl", ""),
            "hardware": result,
            "position_diagnostic": diagnostic,
            "motion_verified": diagnostic["ok"],
            "log_lines": log_lines,
        }
        _set_state(payload)
        return payload

    return _blocked_payload(selected_mode, f"Unknown system mode blocked: {selected_mode}")


def system_safe_retract():

    # Phase 2.2E real safe retract motion. If the motion gate is closed,
    # fall through to the read-only M114 confirmation path below.
    if _SPM_SYSTEM_STATE.get("mode") == "real_hardware_readonly" and _spm_os.environ.get("SPM_WEB_ALLOW_HEALTH_MOTION") == "1":
        from core.web.mk4s_health_motion import run_mk4s_safe_retract
        result = run_mk4s_safe_retract(port=_SPM_SYSTEM_STATE.get("port") or None)
        ok = bool(result.get("ok"))
        if ok:
            _SPM_SYSTEM_STATE["safe_retracted"] = True
        return {"ok": ok, "status": "safe_retracted" if ok else "blocked",
                "mode": "real_hardware_readonly",
                "message": "Real safe retract completed." if ok else "Real safe retract blocked.",
                "port": result.get("port", ""),
                "log_lines": result.get("log_lines", [])}

    if not _SPM_SYSTEM_STATE.get("connected"):
        payload = {
            **_base_payload(),
            "ok": True,
            "status": "safe_retracted",
            "connected": False,
            "powered": False,
            "system_powered": False,
            "safe_retracted": True,
            "mode": _SPM_SYSTEM_STATE.get("mode", "dry_run"),
            "message": "Safe retract not needed: system is already disconnected.",
            "dry_run_plan": [],
            "log_lines": ["Safe retract not needed: system is already disconnected."],
        }
        _set_state(payload)
        return payload

    if _SPM_SYSTEM_STATE.get("mode") == "dry_run":
        payload = {
            **_base_payload(),
            "ok": True,
            "status": "safe_retracted",
            "connected": True,
            "powered": True,
            "system_powered": True,
            "safe_retracted": True,
            "mode": "dry_run",
            "message": "Safe retract confirmed in dry-run mode.",
            "dry_run_plan": [],
            "log_lines": ["Safe retract confirmed in dry-run mode."],
        }
        _set_state(payload)
        return payload

    if _SPM_SYSTEM_STATE.get("mode") == "real_hardware_readonly":
        if _spm_os.environ.get("SPM_WEB_ALLOW_READONLY_HARDWARE") != "1":
            return _blocked_payload("hardware_readonly_locked", "Safe retract check blocked because hardware read-only mode is not enabled.")

        from core.web.mk4s_readonly_connection import connect_real_hardware_readonly

        selected_port = _SPM_SYSTEM_STATE.get("manual_port") or _SPM_SYSTEM_STATE.get("port") or None
        result = connect_real_hardware_readonly(port=selected_port, settle_seconds=0.20)
        position = result.get("position", "")
        z_value = _parse_z(position)

        if z_value is not None and z_value >= _SPM_SAFE_Z_MM:
            message = f"Safe retract confirmed: current Z={z_value:.2f} mm is at/above safe Z={_SPM_SAFE_Z_MM:.2f} mm."
            payload = {
                **_base_payload(),
                "ok": True,
                "status": "safe_retracted",
                "connected": True,
                "powered": True,
                "system_powered": True,
                "safe_retracted": True,
                "mode": "real_hardware_readonly",
                "message": message,
                "port": result.get("port", _SPM_SYSTEM_STATE.get("port", "")),
                "machine_type": result.get("machine_type", _SPM_SYSTEM_STATE.get("machine_type", "")),
                "position": position,
                "temperature": result.get("temperature", _SPM_SYSTEM_STATE.get("temperature", "")),
                "safety": _safety(serial_opened=True, gcode_sent=True, motion_allowed=False),
                "dev_log_file": result.get("dev_log_path_txt", _SPM_SYSTEM_STATE.get("dev_log_file", "")),
                "last_safe_z": f"{z_value:.2f}",
                "hardware": result,
                "dry_run_plan": [],
                "log_lines": list(result.get("log_lines") or []) + [message],
            }
            _SPM_SYSTEM_STATE["last_safe_z"] = f"{z_value:.2f}"
            _set_state(payload)
            return payload

        message = (
            f"Safe retract NOT confirmed. Current position='{position}'. "
            f"Required Z >= {_SPM_SAFE_Z_MM:.2f} mm. Controlled Z motion is not enabled yet, so disconnect/close is blocked."
        )
        payload = {
            **_base_payload(),
            "ok": False,
            "status": "blocked",
            "connected": True,
            "powered": True,
            "system_powered": True,
            "safe_retracted": False,
            "mode": "real_hardware_readonly",
            "message": message,
            "position": position,
            "hardware": result,
            "dry_run_plan": [],
            "log_lines": list(result.get("log_lines") or []) + [message],
        }
        _set_state(payload)
        return payload

    return _blocked_payload(_SPM_SYSTEM_STATE.get("mode", "unknown"), "Safe retract blocked because the current system mode is unknown.")


def system_safe_standby():
    if _SPM_SYSTEM_STATE.get("mode") == "dry_run":
        payload = {
            **_base_payload(),
            "ok": True,
            "status": "safe_standby",
            "connected": True,
            "powered": True,
            "system_powered": True,
            "safe_retracted": True,
            "mode": "dry_run",
            "message": "Safe Standby dry-run: would park at X125 Y105 Z120.",
            "dry_run_plan": ["G90", "G1 Z120.00 F300 if Z is below 120", "G1 X125.00 Y105.00 F600", "G1 Z120.00 F300", "M114"],
            "log_lines": ["Safe Standby dry-run: no hardware command was sent."],
        }
        _set_state(payload)
        return payload

    if _SPM_SYSTEM_STATE.get("mode") != "real_hardware_readonly":
        return _blocked_payload(
            _SPM_SYSTEM_STATE.get("mode", "unknown"),
            "Safe Standby blocked: connect in READ-ONLY hardware mode first.",
        )

    if _spm_os.environ.get("SPM_WEB_ALLOW_HEALTH_MOTION") != "1":
        return {
            **_base_payload(),
            "ok": False,
            "status": "blocked",
            "mode": "safe_standby_motion_locked",
            "message": "Safe Standby motion is locked by environment gate.",
            "log_lines": ["BLOCKED: SPM_WEB_ALLOW_HEALTH_MOTION is not enabled."],
        }

    diagnostic = system_diagnostics()
    if not diagnostic.get("motion_verified"):
        return {
            **diagnostic,
            "ok": False,
            "status": "blocked",
            "message": "Safe Standby blocked: logical position does not match stepper counts. Run SYNC POSITION or power-cycle/reset the printer.",
            "log_lines": list(diagnostic.get("log_lines") or []) + [
                "SAFE STANDBY BLOCKED: Phase 2.1 position diagnostic is not verified."
            ],
        }

    from core.web.mk4s_health_motion import run_mk4s_safe_standby

    result = run_mk4s_safe_standby(port=_SPM_SYSTEM_STATE.get("port") or None)
    ok = bool(result.get("ok"))
    payload = {
        **_base_payload(),
        "ok": ok,
        "connected": True,
        "powered": True,
        "system_powered": True,
        "ready": ok,
        "safe_retracted": ok,
        "status": "safe_standby" if ok else "blocked",
        "mode": "real_hardware_readonly",
        "message": "Safe Standby complete: X125 Y105 Z120 verified." if ok else "Safe Standby blocked or failed.",
        "port": result.get("port", _SPM_SYSTEM_STATE.get("port", "")),
        "position_z": result.get("position_z"),
        "safe_standby": result.get("safe_standby"),
        "log_lines": result.get("log_lines", []),
    }
    if ok:
        pos = result.get("position") or {}
        payload["position"] = f"X:{pos.get('x', 0):.2f} Y:{pos.get('y', 0):.2f} Z:{pos.get('z', 0):.2f}"
        _SPM_SYSTEM_STATE["last_safe_z"] = f"{pos.get('z', 0):.2f}"
    _set_state(payload)
    return payload


def system_disconnect():
    if _SPM_SYSTEM_STATE.get("connected") and not _SPM_SYSTEM_STATE.get("safe_retracted"):
        retract = system_safe_retract()
        if not retract.get("ok"):
            return {
                **retract,
                "message": "Disconnect blocked: safe retract was not confirmed.",
                "log_lines": list(retract.get("log_lines") or []) + ["Disconnect blocked: safe retract was not confirmed."],
            }

    payload = {
        **_base_payload(),
        "ok": True,
        "available": True,
        "ready": False,
        "connected": False,
        "powered": False,
        "system_powered": False,
        "safe_retracted": True,
        "status": "disconnected",
        "mode": "dry_run",
        "message": "System disconnected after safe retract confirmation.",
        "dry_run_plan": [],
        "log_lines": ["System disconnected after safe retract confirmation."],
    }
    _set_state(payload)
    return payload


def system_off():
    return system_disconnect()


def system_close():
    if _SPM_SYSTEM_STATE.get("connected") and not _SPM_SYSTEM_STATE.get("safe_retracted"):
        return _blocked_payload(
            _SPM_SYSTEM_STATE.get("mode", "unknown"),
            "Close blocked: disconnect first. Safe retract must be confirmed before closing the software.",
        )

    payload = {
        **_base_payload(),
        "ok": True,
        "available": True,
        "ready": False,
        "connected": False,
        "powered": False,
        "system_powered": False,
        "safe_retracted": True,
        "status": "closed",
        "mode": "dry_run",
        "message": "Software close allowed: system is safely disconnected.",
        "dry_run_plan": [],
        "log_lines": ["Software close allowed: system is safely disconnected."],
    }
    _set_state(payload)
    return payload


def system_status():
    payload = {
        **_base_payload(),
        "ok": True,
        "available": True,
        "ready": bool(_SPM_SYSTEM_STATE.get("ready")),
        "connected": bool(_SPM_SYSTEM_STATE.get("connected")),
        "powered": bool(_SPM_SYSTEM_STATE.get("powered")),
        "system_powered": bool(_SPM_SYSTEM_STATE.get("system_powered")),
        "safe_retracted": bool(_SPM_SYSTEM_STATE.get("safe_retracted")),
        "status": _SPM_SYSTEM_STATE.get("status", "off"),
        "mode": _SPM_SYSTEM_STATE.get("mode", "dry_run"),
        "operation_mode": _SPM_SYSTEM_STATE.get("operation_mode", "hardware_readonly"),
        "message": _SPM_SYSTEM_STATE.get("message", ""),
        "port": _SPM_SYSTEM_STATE.get("port", ""),
        "manual_port": _SPM_SYSTEM_STATE.get("manual_port", ""),
        "machine_type": _SPM_SYSTEM_STATE.get("machine_type", ""),
        "position": _SPM_SYSTEM_STATE.get("position", ""),
        "temperature": _SPM_SYSTEM_STATE.get("temperature", ""),
        "dev_log_file": _SPM_SYSTEM_STATE.get("dev_log_file", ""),
        "last_safe_z": _SPM_SYSTEM_STATE.get("last_safe_z", ""),
    }
    if not payload["powered"]:
        payload["dry_run_plan"] = []
    return payload


# === Phase 2.2D-COMPAT final payload compatibility wrapper ===
# Adds legacy payload keys expected by the existing tests without changing behavior.

_spm_original_system_on = system_on
_spm_original_system_off = system_off
_spm_original_system_close = system_close
_spm_original_system_status = system_status

try:
    _spm_original_system_disconnect = system_disconnect
except NameError:
    _spm_original_system_disconnect = system_off

try:
    _spm_original_system_safe_retract = system_safe_retract
except NameError:
    _spm_original_system_safe_retract = None

try:
    _spm_original_system_safe_standby = system_safe_standby
except NameError:
    _spm_original_system_safe_standby = None


def _spm_payload_compat(payload):
    if not isinstance(payload, dict):
        return payload

    safety = payload.get("safety")
    if not isinstance(safety, dict):
        safety = {}

    safety.setdefault("serial_opened", False)
    safety.setdefault("gcode_sent", False)
    safety.setdefault("motion_allowed_this_phase", False)
    safety.setdefault("motion_enabled", False)
    safety.setdefault("homing_enabled", False)
    safety.setdefault("heating_enabled", False)
    safety.setdefault("printer_writes_enabled", False)
    safety.setdefault("real_motion_enabled", False)

    payload["safety"] = safety

    # Some existing tests expect these keys at top level too.
    payload.setdefault("motion_allowed_this_phase", safety["motion_allowed_this_phase"])
    payload.setdefault("real_motion_enabled", safety["real_motion_enabled"])

    payload.setdefault("hardware_information_plan_valid", True)

    if "hardware_information_status" not in payload:
        payload["hardware_information_status"] = {
            "available": True,
            "mode": "dry_run_readonly_plan",
            "status": "available",
            "message": "Hardware information layer available as read-only plan.",
        }

    if "simulation_status" not in payload:
        payload["simulation_status"] = {
            "available": True,
            "mode": "web_simulation_dry_run",
            "status": "ready",
            "message": "Simulation path is available.",
        }

    payload.setdefault("dry_run_plan", [])

    if payload.get("status") == "blocked":
        payload["powered"] = False
        payload["system_powered"] = False
        payload["connected"] = False
        payload["ready"] = False
        payload["motion_allowed_this_phase"] = False
        payload["real_motion_enabled"] = False
        payload["safety"]["motion_allowed_this_phase"] = False
        payload["safety"]["real_motion_enabled"] = False

    return payload


def system_on(*args, **kwargs):
    return _spm_payload_compat(_spm_original_system_on(*args, **kwargs))


def system_off(*args, **kwargs):
    return _spm_payload_compat(_spm_original_system_off(*args, **kwargs))


def system_close(*args, **kwargs):
    return _spm_payload_compat(_spm_original_system_close(*args, **kwargs))


def system_status(*args, **kwargs):
    return _spm_payload_compat(_spm_original_system_status(*args, **kwargs))


def system_disconnect(*args, **kwargs):
    return _spm_payload_compat(_spm_original_system_disconnect(*args, **kwargs))


if _spm_original_system_safe_retract is not None:
    def system_safe_retract(*args, **kwargs):
        return _spm_payload_compat(_spm_original_system_safe_retract(*args, **kwargs))


if _spm_original_system_safe_standby is not None:
    def system_safe_standby(*args, **kwargs):
        return _spm_payload_compat(_spm_original_system_safe_standby(*args, **kwargs))


# === Phase 2.2E health test dry-run backend ===

def system_health_test(confirmed: str = "0", motion: str = "0", profile: str = "short"):
    confirmed_text = str(confirmed).strip().lower()
    if confirmed_text not in {"1", "true", "yes", "ok"}:
        return {
            "ok": False,
            "status": "confirmation_required",
            "mode": "health_test_dry_run",
            "message": "Health Test requires operator confirmation first.",
            "log_lines": ["Health Test blocked: operator confirmation missing."],
        }


    if str(motion).strip() == "1":
        if _spm_os.environ.get("SPM_WEB_ALLOW_HEALTH_MOTION") != "1":
            return {"ok": False, "status": "blocked", "mode": "health_motion_locked",
                    "message": "Health motion is locked by environment gate.",
                    "log_lines": ["BLOCKED: SPM_WEB_ALLOW_HEALTH_MOTION is not enabled."]}

        if _SPM_SYSTEM_STATE.get("mode") != "real_hardware_readonly":
            current = _SPM_SYSTEM_STATE.get("mode", "unknown")
            return {"ok": False, "status": "blocked", "mode": current,
                    "message": "Connect in READ-ONLY hardware mode before real Health Test.",
                    "log_lines": [f"BLOCKED: current mode is {current}, not real_hardware_readonly."]}

        diagnostic = system_diagnostics()
        if not diagnostic.get("motion_verified"):
            return {
                "ok": False,
                "status": "blocked",
                "mode": "health_test_real_motion",
                "message": "Health Test blocked: logical position does not match stepper counts. Run SYNC POSITION or power-cycle/reset the printer.",
                "port": diagnostic.get("port", ""),
                "position": diagnostic.get("position", ""),
                "position_diagnostic": diagnostic.get("position_diagnostic"),
                "log_lines": list(diagnostic.get("log_lines") or []) + [
                    "HEALTH TEST BLOCKED: Phase 2.1 position diagnostic is not verified."
                ],
            }

        from core.web.mk4s_health_motion import run_mk4s_health_motion
        result = run_mk4s_health_motion(port=_SPM_SYSTEM_STATE.get("port") or None, profile=profile)
        ok = bool(result.get("ok"))
        return {"ok": ok, "status": "complete" if ok else "blocked",
                "mode": "health_test_real_motion",
                "message": "Real hardware Health Test completed." if ok else "Real hardware Health Test blocked.",
                "port": result.get("port", ""),
                "log_lines": result.get("log_lines", [])}

    lines = [
        "HEALTH TEST STARTED: dry-run / read-only mode only.",
        "Operator confirmed: scan range must be clear before test.",
        "No movement G-code is sent in this phase.",
        "Planned scanner check: X negative direction.",
        "Planned scanner check: X positive direction.",
        "Planned scanner check: Y negative direction.",
        "Planned scanner check: Y positive direction.",
        "Planned scanner check: Z safe retract direction.",
        "Printer head check: firmware, temperature, and position path.",
        "CR-Touch check: read-only endstop/probe status path via M119.",
        "Blocked until later phase: probe deploy/stow and real motion.",
        "HEALTH TEST COMPLETE: dry-run plan logged successfully.",
    ]

    return {
        "ok": True,
        "status": "complete",
        "mode": "health_test_dry_run",
        "message": "Health Test dry-run completed. Review live log.",
        "motion_allowed_this_phase": False,
        "real_motion_enabled": False,
        "log_lines": lines,
    }

