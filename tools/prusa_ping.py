import argparse
import sys
import time

import serial


def read_lines(ser: serial.Serial, seconds: float = 1.0) -> list[str]:
    """Read whatever the printer sends for a short window."""
    end = time.time() + seconds
    lines: list[str] = []
    while time.time() < end:
        try:
            raw = ser.readline()
        except Exception:
            break
        if not raw:
            continue
        s = raw.decode("utf-8", errors="ignore").strip()
        if s:
            lines.append(s)
    return lines


def send_and_wait_ok(ser: serial.Serial, cmd: str, timeout: float = 3.0) -> list[str]:
    """Send one G-code line and collect responses until 'ok' or timeout."""
    ser.write((cmd.strip() + "\n").encode("ascii", errors="ignore"))
    ser.flush()
    out: list[str] = []
    end = time.time() + timeout
    while time.time() < end:
        raw = ser.readline()
        if not raw:
            continue
        s = raw.decode("utf-8", errors="ignore").strip()
        if not s:
            continue
        out.append(s)
        if s.lower().startswith("ok") or s.lower() == "ok":
            break
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Prusa MK4S safe ping (no motion).")
    ap.add_argument("--port", required=True, help="Serial port, e.g. COM5")
    ap.add_argument("--baud", type=int, default=115200, help="Baudrate (default 115200)")
    args = ap.parse_args()

    try:
        ser = serial.Serial(args.port, args.baud, timeout=0.5)
    except Exception as e:
        print(f"ERROR: could not open {args.port} @ {args.baud}: {e}")
        return 2

    try:
        time.sleep(0.8)  # let printer settle
        ser.reset_input_buffer()
        ser.reset_output_buffer()

        # Safe commands: no movement
        # M115 = firmware info; M114 = position report
        print(">> M115")
        for line in send_and_wait_ok(ser, "M115", timeout=4.0):
            print(line)

        print("\n>> M114")
        for line in send_and_wait_ok(ser, "M114", timeout=4.0):
            print(line)

        return 0
    finally:
        try:
            ser.close()
        except Exception:
            pass


if __name__ == "__main__":
    raise SystemExit(main())
