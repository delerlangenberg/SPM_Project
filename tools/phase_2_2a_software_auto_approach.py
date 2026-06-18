from __future__ import annotations

import argparse
import re
import time
from serial import Serial

PORT = "COM5"
BAUD = 115200

CENTER_X = 125.0
CENTER_Y = 105.0

DEFAULT_SURFACE_Z_MM = 55.0
DEFAULT_CLEARANCE_UM = 500.0
DEFAULT_FAST_GUARD_MM = 5.0
DEFAULT_FINE_STEP_UM = 100.0
SAFE_TRAVEL_Z = 80.0
RETRACT_Z = 80.0

Z_COUNTS_PER_MM = 400.0
Z_RESOLUTION_UM = 1000.0 / Z_COUNTS_PER_MM

FEED_XY = 600
FEED_Z_FAST = 300
FEED_Z_SLOW = 60


def round_to_prusa_z_resolution_um(value_um: float) -> float:
    steps = round(value_um / Z_RESOLUTION_UM)
    return steps * Z_RESOLUTION_UM


def read_until_ok(ser: Serial, timeout: float = 15.0) -> list[str]:
    lines = []
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

def send(ser: Serial, cmd: str, timeout: float = 15.0) -> list[str]:
    print(f">>> {cmd}")
    ser.write((cmd + "\n").encode("ascii"))
    ser.flush()
    lines = read_until_ok(ser, timeout=timeout)
    for line in lines:
        print(line)
    return lines


def parse_position(lines: list[str]) -> dict[str, float | None]:
    text = "\n".join(lines)
    out = {"x": None, "y": None, "z": None, "z_count": None}
    for key in ["X", "Y", "Z"]:
        m = re.search(rf"\b{key}:([+-]?\d+(?:\.\d+)?)", text)
        if m:
            out[key.lower()] = float(m.group(1))
    m = re.search(r"Count\s+X:[+-]?\d+\s+Y:[+-]?\d+\s+Z:([+-]?\d+)", text)
    if m:
        out["z_count"] = float(m.group(1))
    return out


def read_z_feedback(ser: Serial, surface_z: float) -> float | None:
    lines = send(ser, "M114", timeout=10)
    pos = parse_position(lines)
    z = pos["z"]
    count = pos["z_count"]

    if z is None:
        print("Z_FEEDBACK: unavailable")
        return None

    above_surface_mm = z - surface_z
    above_surface_um = above_surface_mm * 1000.0

    if count is None:
        print(f"Z_FEEDBACK: Z={z:.3f} mm, above_surface={above_surface_um:.1f} µm")
    else:
        print(
            f"Z_FEEDBACK: Z={z:.3f} mm, CountZ={count:.0f}, "
            f"above_surface={above_surface_um:.1f} µm, "
            f"resolution={Z_RESOLUTION_UM:.1f} µm/count"
        )

    return z

def run_software_approach(args: argparse.Namespace) -> int:
    surface_z = float(args.surface_z)
    clearance_um = round_to_prusa_z_resolution_um(float(args.clearance_um))
    fine_step_um = max(Z_RESOLUTION_UM, round_to_prusa_z_resolution_um(float(args.step_um)))

    target_z = surface_z + clearance_um / 1000.0
    guard_z = surface_z + float(args.fast_guard_mm)

    if clearance_um < 0:
        print("BLOCKED: clearance_um cannot be negative.")
        return 2
    if target_z < surface_z:
        print("BLOCKED: target Z is below declared surface.")
        return 3
    if guard_z <= target_z:
        print("BLOCKED: fast guard must be above target Z.")
        return 4

    print("PHASE 2.2A SOFTWARE AUTO-APPROACH")
    print(f"Surface Z: {surface_z:.3f} mm")
    print(f"Target clearance: {clearance_um:.1f} µm")
    print(f"Target Z: {target_z:.3f} mm")
    print(f"Fast guard Z: {guard_z:.3f} mm")
    print(f"Fine step: {fine_step_um:.1f} µm")
    print(f"Prusa Z resolution used: {Z_RESOLUTION_UM:.1f} µm/count")
    print("Type SOFTWARE_APPROACH to start real hardware movement.")
    if input("> ").strip() != "SOFTWARE_APPROACH":
        print("ABORTED: confirmation text did not match.")
        return 5

    with Serial(PORT, BAUD, timeout=0.2, write_timeout=1.0) as ser:
        time.sleep(0.4)
        ser.reset_input_buffer()

        print("\n=== INITIAL POSITION ===")
        z_now = read_z_feedback(ser, surface_z)
        if z_now is None:
            print("BLOCKED: could not read current Z.")
            return 6

        print("\n=== SAFE CENTER MOVE ===")
        send(ser, "G90")
        send(ser, f"G1 Z{SAFE_TRAVEL_Z:.3f} F{FEED_Z_FAST}", timeout=60)
        send(ser, "M400", timeout=90)
        send(ser, f"G1 X{CENTER_X:.3f} Y{CENTER_Y:.3f} F{FEED_XY}", timeout=60)
        send(ser, "M400", timeout=90)

        print("\n=== FAST APPROACH TO 5 MM GUARD ===")
        send(ser, f"G1 Z{guard_z:.3f} F{FEED_Z_FAST}", timeout=90)
        send(ser, "M400", timeout=90)
        read_z_feedback(ser, surface_z)

        print("\n=== SLOW SOFTWARE APPROACH ===")
        z = guard_z
        step_mm = fine_step_um / 1000.0

        while z - step_mm > target_z:
            z = round(z - step_mm, 4)
            send(ser, f"G1 Z{z:.4f} F{FEED_Z_SLOW}", timeout=30)
            send(ser, "M400", timeout=60)
            read_z_feedback(ser, surface_z)

        send(ser, f"G1 Z{target_z:.4f} F{FEED_Z_SLOW}", timeout=30)
        send(ser, "M400", timeout=60)
        final_z = read_z_feedback(ser, surface_z)

        print("\n=== RETRACT ===")
        send(ser, f"G1 Z{RETRACT_Z:.3f} F{FEED_Z_FAST}", timeout=90)
        send(ser, "M400", timeout=90)
        read_z_feedback(ser, surface_z)

    if final_z is None:
        print("RESULT: APPROACH_DONE_BUT_FINAL_Z_UNREADABLE")
        return 7

    final_clearance_um = (final_z - surface_z) * 1000.0
    print(f"RESULT: OK_SOFTWARE_APPROACH final_clearance={final_clearance_um:.1f} µm")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--surface-z", type=float, default=DEFAULT_SURFACE_Z_MM)
    ap.add_argument("--clearance-um", type=float, default=DEFAULT_CLEARANCE_UM)
    ap.add_argument("--fast-guard-mm", type=float, default=DEFAULT_FAST_GUARD_MM)
    ap.add_argument("--step-um", type=float, default=DEFAULT_FINE_STEP_UM)
    return run_software_approach(ap.parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
