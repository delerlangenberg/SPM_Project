"""Controlled real MK4S raster scan runner for the desktop operator software."""

from __future__ import annotations

import os
import re
import time
from dataclasses import dataclass
from threading import Event
from typing import Callable, Any

from serial import Serial

from core.system.hardware_initialized_profile import get_motion_controller_settings, load_hardware_initialized_profile
from core.web.spm_scan_simulation import WebScanProfile, raster_line_coordinates


_REAL_SCAN_STOP = Event()
_REAL_SCAN_PAUSE = Event()


@dataclass(frozen=True)
class RealScanPoint:
    point_index: int
    line_index: int
    x: float
    y: float
    z_feedback: float
    measured_z: float
    commanded_z: float
    surface_height: float
    feedback_error: float
    feedback_source: str


@dataclass(frozen=True)
class FoilTapConfig:
    table_z_mm: float = 0.0
    z_setpoint_mm: float = 0.0
    tapping_range_mm: float = 20.0
    tap_step_fast_mm: float = 1.0
    tap_step_fine_mm: float = 0.25
    fine_zone_mm: float = 3.0
    approach_speed_mm_s: float = 2.0
    retract_after_tap_mm: float = 3.0
    full_retract_z_mm: float = 120.0
    contact_source: str = "M119_z_min_experimental"
    abort_on_no_contact: bool = True

    @property
    def tap_min_z_mm(self) -> float:
        return self.z_setpoint_mm

    @property
    def tap_start_z_mm(self) -> float:
        return self.z_setpoint_mm + self.tapping_range_mm


def request_real_scan_stop() -> None:
    _REAL_SCAN_STOP.set()


def clear_real_scan_stop() -> None:
    _REAL_SCAN_STOP.clear()


def real_scan_stop_requested() -> bool:
    return _REAL_SCAN_STOP.is_set()


def request_real_scan_pause() -> None:
    _REAL_SCAN_PAUSE.set()


def clear_real_scan_pause() -> None:
    _REAL_SCAN_PAUSE.clear()


def real_scan_paused() -> bool:
    return _REAL_SCAN_PAUSE.is_set()


def real_scan_allowed() -> bool:
    return os.getenv("SPM_WEB_ALLOW_REAL_SCAN", "").strip().lower() in {"1", "true", "yes"}


def foil_tap_allowed() -> bool:
    return os.getenv("SPM_WEB_ALLOW_FOIL_TAP", "").strip().lower() in {"1", "true", "yes"}


def _motion_limits() -> dict[str, float]:
    profile = load_hardware_initialized_profile()
    limits = profile["hardware_initialized_profile"]["motion_limits"]
    return {
        "x_min": float(limits["x_min"]),
        "x_max": float(limits["x_max"]),
        "y_min": float(limits["y_min"]),
        "y_max": float(limits["y_max"]),
        "z_min": float(limits["z_min"]),
        "z_max": float(limits["z_max"]),
    }


def validate_real_scan_profile(profile: WebScanProfile) -> None:
    profile.validate()
    limits = _motion_limits()
    if profile.x_min < limits["x_min"] or profile.x_max > limits["x_max"]:
        raise ValueError(f"X scan range {profile.x_min:.2f}..{profile.x_max:.2f} is outside hardware limits.")
    if profile.y_min < limits["y_min"] or profile.y_max > limits["y_max"]:
        raise ValueError(f"Y scan range {profile.y_min:.2f}..{profile.y_max:.2f} is outside hardware limits.")
    if profile.z_setpoint < limits["z_min"] or profile.z_setpoint > limits["z_max"]:
        raise ValueError(f"Z setpoint {profile.z_setpoint:.2f} is outside hardware limits.")


def validate_foil_tap_config(config: FoilTapConfig) -> None:
    limits = _motion_limits()
    if config.tapping_range_mm <= 0:
        raise ValueError("tapping_range_mm must be positive")
    if config.table_z_mm < limits["z_min"]:
        raise ValueError(f"table_z_mm {config.table_z_mm:.2f} is outside hardware limits.")
    if config.tap_min_z_mm < limits["z_min"] or config.tap_start_z_mm > limits["z_max"]:
        raise ValueError(
            f"Tap Z range {config.tap_min_z_mm:.2f}..{config.tap_start_z_mm:.2f} is outside hardware limits."
        )
    if config.full_retract_z_mm < config.tap_start_z_mm or config.full_retract_z_mm > limits["z_max"]:
        raise ValueError("full_retract_z_mm must be at or above tap_start_z_mm and inside hardware limits.")
    if (
        config.tap_step_fast_mm <= 0
        or config.tap_step_fine_mm <= 0
        or config.retract_after_tap_mm <= 0
        or config.approach_speed_mm_s <= 0
    ):
        raise ValueError("Tap step, approach speed, and retract distances must be positive")


def _linspace(start: float, stop: float, points: int) -> list[float]:
    if points == 1:
        return [start]
    step = (stop - start) / (points - 1)
    return [start + index * step for index in range(points)]


def real_scan_plan(profile: WebScanProfile) -> dict[str, Any]:
    validate_real_scan_profile(profile)
    return {
        "mode": "constant_z_real_m114_raster",
        "x_min": profile.x_min,
        "x_max": profile.x_max,
        "y_min": profile.y_min,
        "y_max": profile.y_max,
        "x_points": profile.x_points,
        "y_lines": profile.y_points,
        "z_setpoint": profile.z_setpoint,
        "scan_direction": profile.scan_direction,
        "point_count": profile.x_points * profile.y_points,
        "execution_gate": "SPM_WEB_ALLOW_REAL_SCAN=1",
    }


def _read_until_ok(ser: Serial, timeout: float = 8.0) -> list[str]:
    lines: list[str] = []
    end = time.time() + timeout
    while time.time() < end:
        raw = ser.readline()
        if not raw:
            continue
        line = raw.decode("utf-8", errors="replace").strip()
        if not line:
            continue
        lines.append(line)
        if line.lower().startswith("echo:busy"):
            end = time.time() + timeout
            continue
        if line == "ok" or line.startswith("ok "):
            return lines
    lines.append("TIMEOUT waiting for ok")
    return lines


def _send(ser: Serial, command: str, timeout: float = 8.0) -> list[str]:
    ser.write((command + "\n").encode("ascii", errors="replace"))
    ser.flush()
    return _read_until_ok(ser, timeout=timeout)


def _parse_xyz(lines: list[str]) -> dict[str, float] | None:
    joined = "\n".join(lines)
    values: dict[str, float] = {}
    for axis in ("X", "Y", "Z"):
        match = re.search(rf"\b{axis}:([+-]?\d+(?:\.\d+)?)", joined)
        if not match:
            return None
        values[axis.lower()] = float(match.group(1))
    return values


def _m119_contact_detected(lines: list[str]) -> bool:
    for line in lines:
        match = re.search(r"\bz_min:\s*(\w+)", line, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip().lower() not in {"open", "false", "0"}
    return False


def _tap_z_values(config: FoilTapConfig) -> list[float]:
    values: list[float] = []
    z = config.tap_start_z_mm
    while z > config.tap_min_z_mm:
        distance_to_min = z - config.tap_min_z_mm
        step = config.tap_step_fine_mm if distance_to_min <= config.fine_zone_mm else config.tap_step_fast_mm
        z = max(config.tap_min_z_mm, z - step)
        values.append(round(z, 4))
    return values


def run_real_constant_z_scan(
    profile: WebScanProfile,
    *,
    port: str | None = None,
    scan_speed_mm_s: float = 5.0,
    on_point: Callable[[dict[str, float]], None] | None = None,
) -> dict[str, Any]:
    validate_real_scan_profile(profile)
    if not real_scan_allowed():
        return {
            "ok": False,
            "status": "motion_locked",
            "message": "Real scan is locked. Launch with SPM_WEB_ALLOW_REAL_SCAN=1.",
            "plan": real_scan_plan(profile),
            "log_lines": ["REAL SCAN BLOCKED: SPM_WEB_ALLOW_REAL_SCAN is not enabled."],
        }

    clear_real_scan_stop()
    clear_real_scan_pause()
    settings = get_motion_controller_settings()
    selected_port = port or str(settings["port"])
    feedrate = max(30.0, min(float(scan_speed_mm_s), 50.0) * 60.0)
    log_lines = [
        f"REAL SCAN: opening {selected_port}.",
        f"REAL SCAN: constant Z={profile.z_setpoint:.3f} mm, {profile.x_points} points x {profile.y_points} lines.",
    ]
    rows: list[list[dict[str, float]]] = []

    with Serial(selected_port, int(settings["baudrate"]), timeout=0.25, write_timeout=1.0) as ser:
        time.sleep(0.4)
        ser.reset_input_buffer()
        for command in ("M114", "G90", f"G1 Z{profile.z_setpoint:.3f} F300", "M400"):
            if real_scan_stop_requested():
                return {"ok": False, "status": "stopped", "message": "Real scan stopped before raster.", "log_lines": log_lines}
            lines = _send(ser, command, timeout=90.0 if command == "M400" or command.startswith("G1 ") else 8.0)
            log_lines.extend([f">>> {command}", *lines])

        for line_index in range(profile.y_points):
            coordinates, line_direction = raster_line_coordinates(profile, line_index)
            row: list[dict[str, float]] = []
            for point_index, (x, y) in enumerate(coordinates):
                while real_scan_paused() and not real_scan_stop_requested():
                    time.sleep(0.05)
                if real_scan_stop_requested():
                    log_lines.append("REAL SCAN STOPPED: operator stop requested.")
                    return {"ok": False, "status": "stopped", "message": "Real scan stopped by operator.", "lines": rows, "log_lines": log_lines}
                move = f"G1 X{x:.3f} Y{y:.3f} F{feedrate:.0f}"
                log_lines.extend([f">>> {move}", *_send(ser, move, timeout=60.0)])
                log_lines.extend([">>> M400", *_send(ser, "M400", timeout=90.0)])
                readback = _send(ser, "M114", timeout=8.0)
                log_lines.extend([">>> M114", *readback])
                xyz = _parse_xyz(readback)
                if xyz is None:
                    return {
                        "ok": False,
                        "status": "failed",
                        "message": "Real scan failed: could not parse M114 position.",
                        "lines": rows,
                        "log_lines": log_lines,
                    }
                point = RealScanPoint(
                    point_index=point_index,
                    line_index=line_index,
                    x=float(xyz["x"]),
                    y=float(xyz["y"]),
                    z_feedback=float(xyz["z"]),
                    measured_z=float(xyz["z"]),
                    commanded_z=float(profile.z_setpoint),
                    surface_height=float(xyz["z"]) - profile.z_setpoint,
                    feedback_error=0.0,
                    feedback_source="M114_exact_z_readback",
                )
                payload = dict(point.__dict__)
                row.append(payload)
                if on_point is not None:
                    on_point(payload)
            rows.append(row)

    return {
        "ok": True,
        "status": "complete",
        "message": f"Real constant-Z scan complete: {profile.x_points} points x {profile.y_points} lines.",
        "lines": rows,
        "plan": real_scan_plan(profile),
        "log_lines": [*log_lines, "REAL SCAN COMPLETE."],
    }


def run_real_foil_tap_scan(
    profile: WebScanProfile,
    config: FoilTapConfig,
    *,
    port: str | None = None,
    scan_speed_mm_s: float = 5.0,
    on_point: Callable[[dict[str, float]], None] | None = None,
) -> dict[str, Any]:
    validate_real_scan_profile(profile)
    validate_foil_tap_config(config)
    if not real_scan_allowed() or not foil_tap_allowed():
        return {
            "ok": False,
            "status": "motion_locked",
            "message": "Foil tap scan is locked. Launch with SPM_WEB_ALLOW_REAL_SCAN=1 and SPM_WEB_ALLOW_FOIL_TAP=1.",
            "log_lines": ["FOIL TAP BLOCKED: real scan and foil tap gates are not both enabled."],
        }

    clear_real_scan_stop()
    clear_real_scan_pause()
    settings = get_motion_controller_settings()
    selected_port = port or str(settings["port"])
    feedrate_xy = max(30.0, min(float(scan_speed_mm_s), 50.0) * 60.0)
    feedrate_z = max(3.0, min(float(config.approach_speed_mm_s), 40.0) * 60.0)
    feedrate_z_fine = max(3.0, min(float(config.approach_speed_mm_s), 0.5) * 60.0)
    rows: list[list[dict[str, float]]] = []
    log_lines = [
        f"FOIL TAP: opening {selected_port}.",
        f"FOIL TAP: {profile.x_points} points x {profile.y_points} lines over "
        f"X {profile.x_min:.2f}..{profile.x_max:.2f}, Y {profile.y_min:.2f}..{profile.y_max:.2f}.",
        f"FOIL TAP: table Z={config.table_z_mm:.2f}; approach {config.tap_start_z_mm:.2f} down to "
        f"{config.tap_min_z_mm:.2f}; approach speed={config.approach_speed_mm_s:.2f} mm/s; "
        f"full retract Z={config.full_retract_z_mm:.2f}; source={config.contact_source}.",
    ]

    with Serial(selected_port, int(settings["baudrate"]), timeout=0.25, write_timeout=1.0) as ser:
        time.sleep(0.4)
        ser.reset_input_buffer()
        for command in (
            "M114",
            "G90",
            f"G1 Z{config.full_retract_z_mm:.3f} F600",
            "M400",
            f"G1 X{profile.x_min:.3f} Y{profile.y_min:.3f} F{feedrate_xy:.0f}",
            "M400",
        ):
            if real_scan_stop_requested():
                return {"ok": False, "status": "stopped", "message": "Foil tap stopped before raster.", "log_lines": log_lines}
            lines = _send(ser, command, timeout=90.0 if command == "M400" or command.startswith("G1 ") else 8.0)
            log_lines.extend([f">>> {command}", *lines])
        log_lines.append("FOIL TAP: scanner pre-positioned to XY minimum before first approach.")

        z_values = _tap_z_values(config)
        for line_index in range(profile.y_points):
            coordinates, line_direction = raster_line_coordinates(profile, line_index)
            row: list[dict[str, float]] = []
            for point_index, (x, y) in enumerate(coordinates):
                while real_scan_paused() and not real_scan_stop_requested():
                    time.sleep(0.05)
                if real_scan_stop_requested():
                    log_lines.append("FOIL TAP STOPPED: operator stop requested.")
                    return {"ok": False, "status": "stopped", "message": "Foil tap stopped by operator.", "lines": rows, "log_lines": log_lines}

                move_xy = f"G1 X{x:.3f} Y{y:.3f} F{feedrate_xy:.0f}"
                log_lines.extend([f">>> {move_xy}", *_send(ser, move_xy, timeout=60.0)])
                log_lines.extend([">>> M400", *_send(ser, "M400", timeout=90.0)])
                start_cmd = f"G1 Z{config.tap_start_z_mm:.3f} F300"
                log_lines.extend([f">>> {start_cmd}", *_send(ser, start_cmd, timeout=90.0)])
                log_lines.extend([">>> M400", *_send(ser, "M400", timeout=90.0)])

                contact_detected = False
                contact_z = config.tap_min_z_mm
                xyz = {"x": float(x), "y": float(y), "z": config.tap_min_z_mm}
                tap_count = 0
                for z in z_values:
                    if real_scan_stop_requested():
                        log_lines.append("FOIL TAP STOPPED: operator stop requested during Z tap.")
                        return {"ok": False, "status": "stopped", "message": "Foil tap stopped by operator.", "lines": rows, "log_lines": log_lines}
                    z_feedrate = feedrate_z_fine if (z - config.tap_min_z_mm) <= config.fine_zone_mm else feedrate_z
                    z_cmd = f"G1 Z{z:.3f} F{z_feedrate:.0f}"
                    log_lines.extend([f">>> {z_cmd}", *_send(ser, z_cmd, timeout=60.0)])
                    log_lines.extend([">>> M400", *_send(ser, "M400", timeout=90.0)])
                    m119 = _send(ser, "M119", timeout=8.0)
                    log_lines.extend([">>> M119", *m119])
                    readback = _send(ser, "M114", timeout=8.0)
                    log_lines.extend([">>> M114", *readback])
                    parsed = _parse_xyz(readback)
                    if parsed is not None:
                        xyz = parsed
                    tap_count += 1
                    if _m119_contact_detected(m119):
                        contact_detected = True
                        contact_z = float(xyz["z"])
                        break

                retract_z = config.full_retract_z_mm
                retract_cmd = f"G1 Z{retract_z:.3f} F300"
                log_lines.extend([f">>> {retract_cmd}", *_send(ser, retract_cmd, timeout=60.0)])
                log_lines.extend([">>> M400", *_send(ser, "M400", timeout=90.0)])

                point = {
                    "point_index": point_index,
                    "line_index": line_index,
                    "x": float(xyz["x"]),
                    "y": float(xyz["y"]),
                    "z_feedback": float(contact_z),
                    "measured_z": float(contact_z),
                    "commanded_z": float(config.tap_start_z_mm),
                    "surface_height": float(contact_z) - float(config.table_z_mm),
                    "feedback_error": 0.0 if contact_detected else 1.0,
                    "feedback_source": config.contact_source,
                    "contact_detected": float(1 if contact_detected else 0),
                    "tap_count": float(tap_count),
                    "retract_z": float(retract_z),
                    "scan_direction": line_direction,
                }
                row.append(point)
                if on_point is not None:
                    on_point(point)
                if not contact_detected and config.abort_on_no_contact:
                    rows.append(row)
                    log_lines.append(
                        f"FOIL TAP ABORTED: no contact before Z={config.tap_min_z_mm:.3f} at "
                        f"line {line_index + 1}, point {point_index + 1}."
                    )
                    return {
                        "ok": False,
                        "status": "no_contact",
                        "message": (
                            "Foil tap aborted: no contact was detected before the configured Z search lower limit. "
                            "Lower the Z setpoint/search limit below the expected surface height or verify the contact feedback channel."
                        ),
                        "lines": rows,
                        "log_lines": log_lines,
                    }
            rows.append(row)

    return {
        "ok": True,
        "status": "complete",
        "message": f"Foil tap scan complete: {profile.x_points} points x {profile.y_points} lines.",
        "lines": rows,
        "log_lines": [*log_lines, "FOIL TAP COMPLETE."],
    }
