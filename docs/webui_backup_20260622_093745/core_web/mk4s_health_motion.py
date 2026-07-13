from __future__ import annotations

import re
import time
import json
from pathlib import Path
from serial import Serial
from serial.tools import list_ports

PRUSA_USB_VID = "VID:PID=2C99:"
PRUSA_USB_PID_ALLOWLIST = {"000D", "001A"}
SAFE_Z_MM = 100.0
PROFILE_PATH = Path("config/spm_hardware_initialized_profile.json")


def _choose_port(port: str | None = None) -> tuple[str, list[str]]:
    log: list[str] = []
    if port:
        log.append(f"Health motion requested manual port: {port}")
        return port, log

    ports = list(list_ports.comports())
    for p in ports:
        hwid = str(getattr(p, "hwid", ""))
        desc = str(getattr(p, "description", ""))
        log.append(f"Port candidate: {p.device} | {desc} | {hwid}")
        matched_pid = next((pid for pid in PRUSA_USB_PID_ALLOWLIST if f"{PRUSA_USB_VID}{pid}" in hwid), "")
        if matched_pid:
            log.append(f"Selected Prusa port by VID/PID {matched_pid}: {p.device}")
            return p.device, log

    raise RuntimeError("No Prusa MK4S USB serial port found.")


def _read_until_ok(ser: Serial, timeout: float = 6.0) -> list[str]:
    lines: list[str] = []
    end = time.time() + timeout

    while time.time() < end:
        raw = ser.readline()
        if not raw:
            continue

        line = raw.decode("utf-8", errors="replace").strip()
        if line:
            lines.append(line)

        if line == "ok" or line.startswith("ok "):
            return lines

    lines.append("TIMEOUT waiting for ok")
    return lines

def _send(ser: Serial, command: str, timeout: float = 6.0) -> list[str]:
    out = [f">>> {command}"]
    ser.write((command + "\n").encode("ascii"))
    ser.flush()
    out.extend(_read_until_ok(ser, timeout=timeout))
    return out


def _parse_z(lines: list[str]) -> float | None:
    joined = "\n".join(lines)
    match = re.search(r"\bZ:([+-]?\d+(?:\.\d+)?)", joined)
    if not match:
        return None
    return float(match.group(1))


def _parse_counts(lines: list[str]) -> dict[str, int] | None:
    joined = "\n".join(lines)
    match = re.search(r"Count\s+X:([+-]?\d+)\s+Y:([+-]?\d+)\s+Z:([+-]?\d+)", joined)
    if not match:
        return None
    return {"x": int(match.group(1)), "y": int(match.group(2)), "z": int(match.group(3))}


def _counts_to_position(counts: dict[str, int]) -> dict[str, float]:
    return {
        "x": counts["x"] / 100.0,
        "y": counts["y"] / 100.0,
        "z": counts["z"] / 400.0,
    }


def _motion_limits() -> dict[str, float]:
    profile = json.loads(PROFILE_PATH.read_text(encoding="utf-8-sig"))
    limits = profile["hardware_initialized_profile"]["motion_limits"]
    return {
        "x_min": float(limits["x_min"]),
        "x_max": float(limits["x_max"]),
        "y_min": float(limits["y_min"]),
        "y_max": float(limits["y_max"]),
        "z_min": float(limits["z_min"]),
        "z_max": float(limits["z_max"]),
    }


def _test_range_blockers(position: dict[str, float], *, x_mm: float, y_mm: float, z_mm: float) -> list[str]:
    limits = _motion_limits()
    checks = [
        ("X", position["x"], x_mm, limits["x_min"], limits["x_max"]),
        ("Y", position["y"], y_mm, limits["y_min"], limits["y_max"]),
        ("Z", position["z"], z_mm, limits["z_min"], limits["z_max"]),
    ]
    blockers: list[str] = []
    for axis, current, delta, min_value, max_value in checks:
        low = current - delta
        high = current + delta
        if low < min_value or high > max_value:
            blockers.append(
                f"{axis} axis lacks +/-{delta:.1f} mm clearance: current={current:.2f}, "
                f"test range={low:.2f}..{high:.2f}, allowed={min_value:.2f}..{max_value:.2f}."
            )
    return blockers


def _read_position_counts(ser: Serial, log: list[str]) -> dict[str, int] | None:
    lines = _send(ser, "M114", timeout=6.0)
    log.extend(lines)
    return _parse_counts(lines)


def _verified_relative_leg(
    ser: Serial,
    log: list[str],
    *,
    axis: str,
    distance_mm: float,
    feedrate: int,
) -> bool:
    before = _read_position_counts(ser, log)
    if before is None:
        log.append(f"BLOCKED: could not read {axis.upper()} count before health movement.")
        return False

    axis_key = axis.lower()
    command = f"G1 {axis.upper()}{distance_mm:.1f} F{feedrate}"
    log.extend(_send(ser, command, timeout=20.0))
    log.extend(_send(ser, "M400", timeout=90.0))
    after = _read_position_counts(ser, log)
    if after is None:
        log.append(f"BLOCKED: could not read {axis.upper()} count after health movement.")
        return False

    if after[axis_key] == before[axis_key]:
        log.append(
            f"FAILED: {axis.upper()} physical count did not change after {command}. "
            f"before={before[axis_key]} after={after[axis_key]}"
        )
        return False

    log.append(
        f"VERIFIED: {axis.upper()} count changed after {command}: "
        f"{before[axis_key]} -> {after[axis_key]}"
    )
    return True


def run_mk4s_health_motion(port: str | None = None, profile: str = "short") -> dict:
    chosen, log = _choose_port(port)
    log.append("HEALTH MOTION: opening serial connection.")
    with Serial(chosen, 115200, timeout=0.2, write_timeout=1.0) as ser:
        time.sleep(0.4)
        ser.reset_input_buffer()

        for cmd in ["M115", "M105", "M119", "M114"]:
            log.extend(_send(ser, cmd, timeout=6.0))

        z_value = _parse_z(log)
        initial_counts = _parse_counts(log)
        if z_value is None:
            return {"ok": False, "port": chosen, "log_lines": log + ["BLOCKED: could not read current Z."]}
        if initial_counts is None:
            return {"ok": False, "port": chosen, "log_lines": log + ["BLOCKED: could not read Count X/Y/Z."]}

        if z_value < SAFE_Z_MM:
            msg = f"BLOCKED: current Z={z_value:.2f} mm is below safe Z={SAFE_Z_MM:.2f} mm."
            return {"ok": False, "port": chosen, "position_z": z_value, "log_lines": log + [msg]}

        long_mode = str(profile).lower() in {"long", "longer", "extended"}
        x_mm = 62.5 if long_mode else 10.0
        y_mm = 52.5 if long_mode else 10.0
        z_mm = 55.0 if long_mode else 10.0

        log.append(f"SAFE Z CONFIRMED: Z={z_value:.2f} mm.")
        position = _counts_to_position(initial_counts)
        range_blockers = _test_range_blockers(position, x_mm=x_mm, y_mm=y_mm, z_mm=z_mm)
        if range_blockers:
            return {
                "ok": False,
                "port": chosen,
                "position_z": z_value,
                "log_lines": log + [
                    "BLOCKED: XYZ axes health test cannot run from the current position.",
                    *range_blockers,
                    "Move the Prusa to a safe central XYZ position with the printer controls, then rerun Phase 2.1 DIAGNOSE.",
                ],
            }

        log.append(f"HEALTH PROFILE: {profile}; visible XYZ axes round-trip travel; X +/-{x_mm:.1f} mm; Y +/-{y_mm:.1f} mm; Z +/-{z_mm:.1f} mm.")

        log.extend(_send(ser, "M400", timeout=90.0))
        log.extend(_send(ser, "G91", timeout=20.0))

        for axis, distance, feedrate in (
            ("X", x_mm, 600),
            ("X", -x_mm, 600),
            ("Y", y_mm, 600),
            ("Y", -y_mm, 600),
            ("Z", z_mm, 300),
            ("Z", -z_mm, 300),
        ):
            if not _verified_relative_leg(ser, log, axis=axis, distance_mm=distance, feedrate=feedrate):
                log.extend(_send(ser, "G90", timeout=20.0))
                return {"ok": False, "port": chosen, "position_z": z_value, "log_lines": log}

        for cmd in ["G90", "M114", "M119"]:
            log.extend(_send(ser, cmd, timeout=20.0))

    log.append("HEALTH MOTION COMPLETE: XYZ axes hardware health movement completed.")
    return {"ok": True, "port": chosen, "position_z": z_value, "log_lines": log}

SAFE_RETRACT_TARGET_Z = 150.0
SAFE_RETRACT_MAX_Z = 220.0
SAFE_STANDBY_X = 125.0
SAFE_STANDBY_Y = 105.0
SAFE_STANDBY_Z = 120.0
SAFE_STANDBY_XY_FEEDRATE = 600
SAFE_STANDBY_Z_FEEDRATE = 300


def _axis_mismatch_from_counts(lines: list[str], tolerance_mm: float = 0.02) -> list[str]:
    joined = "\n".join(lines)
    counts = _parse_counts(lines)
    if counts is None:
        return ["missing Count X/Y/Z from M114"]

    physical = _counts_to_position(counts)
    mismatches: list[str] = []
    for axis in ("x", "y", "z"):
        match = re.search(rf"\b{axis.upper()}:([+-]?\d+(?:\.\d+)?)", joined)
        if not match:
            mismatches.append(f"{axis.upper()}: missing logical coordinate")
            continue
        logical = float(match.group(1))
        delta = logical - physical[axis]
        if abs(delta) > tolerance_mm:
            mismatches.append(
                f"{axis.upper()}: logical {logical:.2f} mm, count-derived {physical[axis]:.2f} mm, delta {delta:+.2f} mm"
            )
    return mismatches


def _target_blockers(*, x: float, y: float, z: float) -> list[str]:
    limits = _motion_limits()
    checks = [
        ("X", x, limits["x_min"], limits["x_max"]),
        ("Y", y, limits["y_min"], limits["y_max"]),
        ("Z", z, limits["z_min"], limits["z_max"]),
    ]
    blockers: list[str] = []
    for axis, value, low, high in checks:
        if value < low or value > high:
            blockers.append(f"{axis} target {value:.2f} mm is outside allowed range {low:.2f}..{high:.2f} mm.")
    return blockers


def run_mk4s_safe_standby(port: str | None = None) -> dict:
    chosen, log = _choose_port(port)
    log.append("SAFE STANDBY: opening serial connection.")
    blockers = _target_blockers(x=SAFE_STANDBY_X, y=SAFE_STANDBY_Y, z=SAFE_STANDBY_Z)
    if blockers:
        return {"ok": False, "port": chosen, "log_lines": log + ["BLOCKED: safe standby target is invalid.", *blockers]}

    with Serial(chosen, 115200, timeout=0.2, write_timeout=1.0) as ser:
        time.sleep(0.4)
        ser.reset_input_buffer()

        initial_lines = _send(ser, "M114", timeout=6.0)
        log.extend(initial_lines)
        initial_counts = _parse_counts(initial_lines)
        z_value = _parse_z(initial_lines)
        if initial_counts is None or z_value is None:
            return {"ok": False, "port": chosen, "log_lines": log + ["BLOCKED: could not read current M114 position/counts."]}

        mismatches = _axis_mismatch_from_counts(initial_lines)
        if mismatches:
            return {
                "ok": False,
                "port": chosen,
                "log_lines": log + [
                    "BLOCKED: logical position does not match stepper counts. Use SYNC POSITION before Safe Standby.",
                    *mismatches,
                ],
            }

        limits = _motion_limits()
        current = _counts_to_position(initial_counts)
        current_blockers = [
            f"{axis.upper()} current position {current[axis]:.2f} mm is outside machine range {limits[axis + '_min']:.2f}..{limits[axis + '_max']:.2f} mm."
            for axis in ("x", "y", "z")
            if current[axis] < limits[axis + "_min"] or current[axis] > limits[axis + "_max"]
        ]
        if current_blockers:
            return {"ok": False, "port": chosen, "log_lines": log + ["BLOCKED: current position is outside confirmed machine limits.", *current_blockers]}

        log.append(
            f"SAFE STANDBY TARGET: X{SAFE_STANDBY_X:.2f} Y{SAFE_STANDBY_Y:.2f} Z{SAFE_STANDBY_Z:.2f} mm."
        )
        log.extend(_send(ser, "G90", timeout=20.0))

        if z_value < SAFE_STANDBY_Z:
            log.append(f"SAFE STANDBY: lifting Z first {z_value:.2f} -> {SAFE_STANDBY_Z:.2f} mm.")
            log.extend(_send(ser, f"G1 Z{SAFE_STANDBY_Z:.2f} F{SAFE_STANDBY_Z_FEEDRATE}", timeout=90.0))
            log.extend(_send(ser, "M400", timeout=90.0))
        else:
            log.append(f"SAFE STANDBY: Z already at/above target ({z_value:.2f} mm); moving XY while elevated.")

        log.extend(_send(ser, f"G1 X{SAFE_STANDBY_X:.2f} Y{SAFE_STANDBY_Y:.2f} F{SAFE_STANDBY_XY_FEEDRATE}", timeout=90.0))
        log.extend(_send(ser, "M400", timeout=90.0))

        if abs(z_value - SAFE_STANDBY_Z) > 0.02:
            log.extend(_send(ser, f"G1 Z{SAFE_STANDBY_Z:.2f} F{SAFE_STANDBY_Z_FEEDRATE}", timeout=90.0))
            log.extend(_send(ser, "M400", timeout=90.0))

        final_lines = _send(ser, "M114", timeout=6.0)
        log.extend(final_lines)
        final_counts = _parse_counts(final_lines)
        if final_counts is None:
            return {"ok": False, "port": chosen, "log_lines": log + ["FAILED: safe standby could not read final stepper counts."]}

        final = _counts_to_position(final_counts)
        target = {"x": SAFE_STANDBY_X, "y": SAFE_STANDBY_Y, "z": SAFE_STANDBY_Z}
        errors = [
            f"{axis.upper()} final {final[axis]:.2f} mm differs from target {target[axis]:.2f} mm."
            for axis in ("x", "y", "z")
            if abs(final[axis] - target[axis]) > 0.05
        ]
        if errors:
            return {"ok": False, "port": chosen, "position": final, "log_lines": log + ["FAILED: safe standby target did not verify.", *errors]}

        log.extend(_send(ser, "M119", timeout=20.0))

    log.append("SAFE STANDBY COMPLETE: hardware is centered and parked at default safe Z.")
    return {
        "ok": True,
        "port": chosen,
        "position": final,
        "position_z": final["z"],
        "safe_standby": {"x": SAFE_STANDBY_X, "y": SAFE_STANDBY_Y, "z": SAFE_STANDBY_Z},
        "log_lines": log,
    }


def run_mk4s_safe_retract(port: str | None = None) -> dict:
    chosen, log = _choose_port(port)
    log.append("SAFE RETRACT: opening serial connection.")

    with Serial(chosen, 115200, timeout=0.2, write_timeout=1.0) as ser:
        time.sleep(0.4)
        ser.reset_input_buffer()

        initial_lines = _send(ser, "M114", timeout=6.0)
        log.extend(initial_lines)
        z_value = _parse_z(initial_lines)
        initial_counts = _parse_counts(initial_lines)

        if z_value is None:
            return {"ok": False, "port": chosen, "log_lines": log + ["BLOCKED: could not read current Z."]}

        if SAFE_RETRACT_TARGET_Z > SAFE_RETRACT_MAX_Z:
            return {"ok": False, "port": chosen, "log_lines": log + ["BLOCKED: safe retract target exceeds max Z."]}

        if z_value >= SAFE_RETRACT_TARGET_Z:
            log.append(f"SAFE RETRACT: current Z={z_value:.2f}; no movement needed.")
            return {"ok": True, "port": chosen, "position_z": z_value, "log_lines": log}

        log.append(f"SAFE RETRACT MOVE: Z {z_value:.2f} -> {SAFE_RETRACT_TARGET_Z:.2f} mm.")
        for cmd in ["G90", f"G1 Z{SAFE_RETRACT_TARGET_Z:.1f} F300", "M400"]:
            cmd_timeout = 90.0 if cmd == "M400" else 20.0
            log.extend(_send(ser, cmd, timeout=cmd_timeout))

        final_lines = _send(ser, "M114", timeout=6.0)
        log.extend(final_lines)
        final_counts = _parse_counts(final_lines)
        if final_counts is None:
            return {"ok": False, "port": chosen, "position_z": z_value, "log_lines": log + ["FAILED: safe retract could not read final stepper counts."]}

        final_count_z_mm = final_counts["z"] / 400.0
        if abs(final_count_z_mm - SAFE_RETRACT_TARGET_Z) > 0.01:
            initial_count_text = "unknown" if initial_counts is None else str(initial_counts["z"])
            return {
                "ok": False,
                "port": chosen,
                "position_z": z_value,
                "log_lines": log + [
                    "FAILED: safe retract did not physically reach target.",
                    f"Target Z={SAFE_RETRACT_TARGET_Z:.2f}; Count Z before={initial_count_text}; Count Z after={final_counts['z']} ({final_count_z_mm:.2f} mm).",
                ],
            }

        log.extend(_send(ser, "M119", timeout=20.0))

    log.append("SAFE RETRACT COMPLETE: hardware Z retract finished.")
    return {"ok": True, "port": chosen, "position_z": SAFE_RETRACT_TARGET_Z, "log_lines": log}
