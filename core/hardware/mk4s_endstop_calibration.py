from __future__ import annotations
import json
import re
import time
from pathlib import Path
from typing import Any
from serial import Serial
from serial.tools import list_ports

PRUSA_USB_VID = "VID:PID=2C99:"
PRUSA_USB_PID_ALLOWLIST = {"000D", "001A"}
PROFILE_PATH = Path("config/spm_hardware_initialized_profile.json")
SAFE_Z_MM = 100.0
HOME_FEEDRATE = 600
TRAVEL_FEEDRATE = 1200


def _choose_port(port: str | None = None) -> tuple[str, list[str]]:
    log: list[str] = []
    if port:
        log.append(f"Calibration using port: {port}")
        return port, log
    for p in list_ports.comports():
        hwid = str(getattr(p, "hwid", ""))
        matched_pid = next(
            (pid for pid in PRUSA_USB_PID_ALLOWLIST if f"{PRUSA_USB_VID}{pid}" in hwid), ""
        )
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


def _parse_endstops(lines: list[str]) -> dict[str, bool]:
    joined = "\n".join(lines)
    results: dict[str, bool] = {}
    pat = re.compile(r"(?:x|X|y|Y|z|Z)_(?:min|max|probe):\s*(1|0|TRIGGERED|open)")
    for match in pat.finditer(joined):
        key = match.group(0).split(":")[0].lower()
        value = match.group(1)
        results[key] = value in {"1", "TRIGGERED"}
    return results


def _parse_counts(lines: list[str]) -> dict[str, int] | None:
    joined = "\n".join(lines)
    match = re.search(r"Count X:([+-]?\d+) Y:([+-]?\d+) Z:([+-]?\d+)", joined)
    if not match:
        return None
    return {"x": int(match.group(1)), "y": int(match.group(2)), "z": int(match.group(3))}


def _counts_to_mm(counts: dict[str, int]) -> dict[str, float]:
    return {
        "x": counts["x"] / 100.0,
        "y": counts["y"] / 100.0,
        "z": counts["z"] / 400.0,
    }


def _load_motion_limits() -> dict[str, float] | None:
    if not PROFILE_PATH.exists():
        return None
    try:
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
    except (KeyError, ValueError, json.JSONDecodeError):
        return None


def run_home_and_verify(port: str | None = None) -> dict[str, Any]:
    "Run G28 auto-home, verify endstops, and record home position."
    chosen, log = _choose_port(port)
    log.append("CALIBRATION: opening serial connection.")
    with Serial(chosen, 115200, timeout=0.2, write_timeout=1.0) as ser:
        time.sleep(0.4)
        ser.reset_input_buffer()
        for cmd in ["M115", "M105", "M119", "M114"]:
            log.extend(_send(ser, cmd, timeout=6.0))
        firmware = ""
        for line in log:
            if "FIRMWARE_NAME:" in line:
                firmware = line
                break
        m119_before = _parse_endstops(log)
        log.append(f"Endstop state before homing: {json.dumps(m119_before)}")
        log.append("CALIBRATION: running G28 (auto-home all axes)...")
        log.extend(_send(ser, "G28", timeout=120.0))
        log.extend(_send(ser, "M400", timeout=90.0))
        log.extend(_send(ser, "M119", timeout=6.0))
        m119_after = _parse_endstops(log)
        log.append(f"Endstop state after G28: {json.dumps(m119_after)}")
        log.extend(_send(ser, "M114", timeout=6.0))
        home_counts = _parse_counts(log)
        home_mm = _counts_to_mm(home_counts) if home_counts else None
        log.append(f"Home position counts: {home_counts}")
        log.append(f"Home position mm: {home_mm}")
        all_triggered = all(m119_after.values()) if m119_after else False
        log.append(f"All endstops triggered after G28: {all_triggered}")
        limits = _load_motion_limits()
        log.extend(_send(ser, "G90", timeout=6.0))
        log.extend(_send(ser, "G1 Z120.0 F300", timeout=30.0))
        log.extend(_send(ser, "M400", timeout=30.0))
        steering = {
            "port": chosen,
            "firmware": firmware,
            "ok": all_triggered,
            "home_counts": home_counts,
            "home_mm": home_mm,
            "endstops_before": m119_before,
            "endstops_after": m119_after,
            "all_endstops_triggered": all_triggered,
            "log_lines": log,
            "motion_limits": limits,
        }
    _save_calibration_results(steering)
    return steering



    return "world"


def _save_calibration_results(data: dict[str, Any]) -> None:
    cal = {
        "last_calibration_date": time.strftime("%Y-%m-%d %H:%M:%S"),
        "port": data.get("port", ""),
        "firmware": data.get("firmware", ""),
        "home_counts": data.get("home_counts"),
        "home_mm": data.get("home_mm"),
        "all_endstops_triggered": data.get("all_endstops_triggered", False),
        "endstops_before_home": {k: v for k, v in (data.get("endstops_before") or {}).items()},
        "endstops_after_home": {k: v for k, v in (data.get("endstops_after") or {}).items()},
    }
    profile = {"spm_calibration": cal}
    cal_path = Path("config/spm_calibration.json")
    cal_path.write_text(json.dumps(profile, indent=2), encoding="utf-8")
    data["log_lines"].append("Calibration saved to config/spm_calibration.json")


def run_repeatability_test(port: str | None = None, iterations: int = 3) -> dict[str, Any]:
    "Home multiple times and verify position repeatability."
    chosen, log = _choose_port(port)
    log.append(f"REPEATABILITY: {iterations} iterations.")
    positions: list[dict[str, int] | None] = []
    with Serial(chosen, 115200, timeout=0.2, write_timeout=1.0) as ser:
        time.sleep(0.4)
        ser.reset_input_buffer()
        for i in range(iterations):
            log.append(f"  Iteration {i+1}/{iterations} - G28...")
            log.extend(_send(ser, "G28", timeout=120.0))
            log.extend(_send(ser, "M400", timeout=60.0))
            log.extend(_send(ser, "M114", timeout=6.0))
            counts = _parse_counts(log)
            positions.append(counts)
            log.append(f"  Counts: {counts}")
            if i < iterations - 1:
                log.extend(_send(ser, "G90", timeout=6.0))
                log.extend(_send(ser, "G1 Z120.0 F300", timeout=30.0))
                log.extend(_send(ser, "M400", timeout=30.0))
    ok = False
    if len(positions) >= 2 and all(p is not None for p in positions):
        first = positions[0]
        ok = all(p == first for p in positions)
    log.append(f"Repeatability: {ok}")
    return {"ok": ok, "port": chosen, "iterations": iterations, "positions": positions, "log_lines": log}


if __name__ == "__main__":
    import sys
    if "--repeatability" in sys.argv:
        result = run_repeatability_test()
    else:
        result = run_home_and_verify()
    for line in result.get("log_lines", []):
        print(line)
    print(f"\nResult: ok={result.get('ok')}")
