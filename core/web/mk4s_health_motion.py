from __future__ import annotations

import re
import time
from serial import Serial
from serial.tools import list_ports

PRUSA_VIDPID = "VID:PID=2C99:000D"
SAFE_Z_MM = 100.0


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
        if PRUSA_VIDPID in hwid:
            log.append(f"Selected Prusa port by VID/PID: {p.device}")
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


def run_mk4s_health_motion(port: str | None = None, profile: str = "short") -> dict:
    chosen, log = _choose_port(port)
    log.append("HEALTH MOTION: opening serial connection.")
    with Serial(chosen, 115200, timeout=0.2, write_timeout=1.0) as ser:
        time.sleep(0.4)
        ser.reset_input_buffer()

        for cmd in ["M115", "M105", "M119", "M114"]:
            log.extend(_send(ser, cmd, timeout=6.0))

        z_value = _parse_z(log)
        if z_value is None:
            return {"ok": False, "port": chosen, "log_lines": log + ["BLOCKED: could not read current Z."]}

        if z_value < SAFE_Z_MM:
            msg = f"BLOCKED: current Z={z_value:.2f} mm is below safe Z={SAFE_Z_MM:.2f} mm."
            return {"ok": False, "port": chosen, "position_z": z_value, "log_lines": log + [msg]}

        long_mode = str(profile).lower() in {"long", "longer", "extended"}
        x_mm = 62.5 if long_mode else 1.0
        y_mm = 52.5 if long_mode else 1.0
        z_mm = 55.0 if long_mode else 1.0

        log.append(f"SAFE Z CONFIRMED: Z={z_value:.2f} mm.")
        log.append(f"HEALTH PROFILE: {profile}; 50 percent max-range travel; X +/-{x_mm:.1f} mm; Y +/-{y_mm:.1f} mm; Z +/-{z_mm:.1f} mm.")

        commands = ["M400", "G91"]
        commands += [f"G1 X{x_mm:.1f} F600", "M400", f"G1 X-{x_mm:.1f} F600", "M400"]
        commands += [f"G1 Y{y_mm:.1f} F600", "M400", f"G1 Y-{y_mm:.1f} F600", "M400"]
        commands += [f"G1 Z{z_mm:.1f} F300", "M400", f"G1 Z-{z_mm:.1f} F300", "M400"]
        commands += ["G90", "M114", "M119"]

        for cmd in commands:
            cmd_timeout = 90.0 if cmd == "M400" else 20.0
            log.extend(_send(ser, cmd, timeout=cmd_timeout))

    log.append("HEALTH MOTION COMPLETE: X/Y/Z hardware health movement completed.")
    return {"ok": True, "port": chosen, "position_z": z_value, "log_lines": log}

SAFE_RETRACT_TARGET_Z = 150.0
SAFE_RETRACT_MAX_Z = 220.0


def run_mk4s_safe_retract(port: str | None = None) -> dict:
    chosen, log = _choose_port(port)
    log.append("SAFE RETRACT: opening serial connection.")

    with Serial(chosen, 115200, timeout=0.2, write_timeout=1.0) as ser:
        time.sleep(0.4)
        ser.reset_input_buffer()

        log.extend(_send(ser, "M114", timeout=6.0))
        z_value = _parse_z(log)

        if z_value is None:
            return {"ok": False, "port": chosen, "log_lines": log + ["BLOCKED: could not read current Z."]}

        if SAFE_RETRACT_TARGET_Z > SAFE_RETRACT_MAX_Z:
            return {"ok": False, "port": chosen, "log_lines": log + ["BLOCKED: safe retract target exceeds max Z."]}

        if z_value >= SAFE_RETRACT_TARGET_Z:
            log.append(f"SAFE RETRACT: current Z={z_value:.2f}; no movement needed.")
            return {"ok": True, "port": chosen, "position_z": z_value, "log_lines": log}

        log.append(f"SAFE RETRACT MOVE: Z {z_value:.2f} -> {SAFE_RETRACT_TARGET_Z:.2f} mm.")
        for cmd in ["G90", f"G1 Z{SAFE_RETRACT_TARGET_Z:.1f} F300", "M400", "M114", "M119"]:
            cmd_timeout = 90.0 if cmd == "M400" else 20.0
            log.extend(_send(ser, cmd, timeout=cmd_timeout))

    log.append("SAFE RETRACT COMPLETE: hardware Z retract finished.")
    return {"ok": True, "port": chosen, "position_z": SAFE_RETRACT_TARGET_Z, "log_lines": log}
