from __future__ import annotations

import re
import time
from serial import Serial

PORT = "COM5"
BAUD = 115200

CENTER_X = 125.0
CENTER_Y = 105.0

SAFE_START_Z = 100.0
START_APPROACH_Z = 80.0
APPROACH_FLOOR_Z = 55.0
RETRACT_Z = 80.0

STEP_MM = 0.5
FEED_Z = 60
FEED_XY = 600


def read_until_ok(ser: Serial, timeout: float = 8.0) -> list[str]:
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


def send(ser: Serial, cmd: str, timeout: float = 8.0) -> list[str]:
    print(f">>> {cmd}")
    ser.write((cmd + "\n").encode("ascii"))
    ser.flush()
    lines = read_until_ok(ser, timeout=timeout)
    for line in lines:
        print(line)
    return lines


def parse_z(lines: list[str]) -> float | None:
    text = "\n".join(lines)
    m = re.search(r"\bZ:([+-]?\d+(?:\.\d+)?)", text)
    return float(m.group(1)) if m else None

def z_probe_triggered(lines: list[str]) -> bool:
    text = "\n".join(lines).lower()
    trigger_words = ["triggered", "trig", "closed"]
    z_lines = [line.lower() for line in lines if "z_" in line.lower() or "probe" in line.lower()]
    return any(any(word in line for word in trigger_words) for line in z_lines)


def main() -> int:
    print("PHASE 2.2A CONTROLLED AUTO-APPROACH TEST")
    print(f"Target center: X{CENTER_X} Y{CENTER_Y}")
    print(f"Approach floor: Z{APPROACH_FLOOR_Z}")
    print("Type APPROACH to start real hardware movement.")
    confirm = input("> ").strip()

    if confirm != "APPROACH":
        print("ABORTED: confirmation text did not match.")
        return 2

    contact_detected = False
    contact_z = None

    with Serial(PORT, BAUD, timeout=0.2, write_timeout=1.0) as ser:
        time.sleep(0.4)
        ser.reset_input_buffer()

        print("\n=== INITIAL READ ===")
        pos_lines = send(ser, "M114")
        z_now = parse_z(pos_lines)

        if z_now is None:
            print("BLOCKED: could not read current Z.")
            return 3

        if z_now < SAFE_START_Z:
            print(f"BLOCKED: current Z={z_now:.2f} is below safe start Z={SAFE_START_Z:.2f}.")
            return 4

        print("\n=== MOVE TO CENTER ABOVE OBJECT ===")
        send(ser, "G90")
        send(ser, f"G1 X{CENTER_X:.1f} Y{CENTER_Y:.1f} F{FEED_XY}", timeout=30)
        send(ser, "M400", timeout=30)
        send(ser, f"G1 Z{START_APPROACH_Z:.1f} F300", timeout=60)
        send(ser, "M400", timeout=60)

        print("\n=== SLOW APPROACH ===")
        z = START_APPROACH_Z
        while z > APPROACH_FLOOR_Z:
            z = max(APPROACH_FLOOR_Z, z - STEP_MM)
            send(ser, f"G1 Z{z:.1f} F{FEED_Z}", timeout=20)
            send(ser, "M400", timeout=30)
            m119 = send(ser, "M119", timeout=8)

            if z_probe_triggered(m119):
                contact_detected = True
                contact_z = z
                print(f"CONTACT_DETECTED_BY_M119 at Z={z:.2f}")
                break

        print("\n=== RETRACT ===")
        send(ser, f"G1 Z{RETRACT_Z:.1f} F300", timeout=60)
        send(ser, "M400", timeout=60)
        final_pos = send(ser, "M114")

    if contact_detected:
        print(f"RESULT: OK_CONTACT_DETECTED_Z={contact_z:.2f}")
        return 0

    print("RESULT: NO_M119_CONTACT_TRIGGER_BEFORE_FLOOR")
    print("Meaning: movement completed, but automatic contact detection is not proven.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
