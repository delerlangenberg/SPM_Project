from __future__ import annotations

import argparse
import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path

SAFE_READONLY_COMMANDS = ["M115", "M105", "M119", "M114"]

FORBIDDEN_PREFIXES = (
    "G0", "G00", "G1", "G01",
    "G28", "G29",
    "M17", "M18", "M80", "M81",
    "M104", "M109", "M140", "M190",
    "M302", "M500", "M501", "M502",
)

PROJECT = Path(__file__).resolve().parents[1]
LOG_DIR = PROJECT / "docs" / "hardware_logs"


def fail(message: str) -> int:
    print(f"ERROR: {message}")
    return 1


def validate_safe_commands() -> None:
    for command in SAFE_READONLY_COMMANDS:
        normalized = command.strip().upper()
        for forbidden in FORBIDDEN_PREFIXES:
            if normalized.startswith(forbidden):
                raise RuntimeError(f"Unsafe command blocked in readonly probe: {command}")


def list_ports() -> int:
    try:
        from serial.tools import list_ports
    except Exception as exc:
        return fail(
            "pyserial is not available. Install/check project environment first. "
            f"Import error: {exc}"
        )

    ports = list(list_ports.comports())

    print("=== AVAILABLE SERIAL PORTS ===")
    if not ports:
        print("NO_PORTS_FOUND")
        print("Check USB cable, printer power, and Windows Device Manager.")
        return 2

    for p in ports:
        print(f"PORT={p.device}")
        print(f"  description={p.description}")
        print(f"  hwid={p.hwid}")

    print("")
    print("Choose the Prusa/MK4S/USB serial COM port above.")
    print("Then run:")
    print(r'  .\.venv\Scripts\python.exe tools\phase_2_2a_mk4s_readonly_probe.py --port COMx')
    print("")
    print("Replace COMx with the actual port, for example COM3 or COM7.")
    return 0


def read_available(ser, seconds: float) -> list[str]:
    lines: list[str] = []
    deadline = time.time() + seconds

    while time.time() < deadline:
        try:
            raw = ser.readline()
        except Exception as exc:
            lines.append(f"<<READ_ERROR: {exc}>>")
            break

        if not raw:
            continue

        text = raw.decode("utf-8", errors="replace").rstrip()
        if text:
            lines.append(text)

    return lines


def send_readonly_command(ser, command: str, timeout_seconds: float) -> list[str]:
    validate_safe_commands()

    command = command.strip().upper()
    if command not in SAFE_READONLY_COMMANDS:
        raise RuntimeError(f"Command not in readonly allowlist: {command}")

    ser.write((command + "\n").encode("ascii"))
    ser.flush()

    lines: list[str] = [f">>> {command}"]
    deadline = time.time() + timeout_seconds

    while time.time() < deadline:
        raw = ser.readline()
        if not raw:
            continue

        text = raw.decode("utf-8", errors="replace").rstrip()
        if not text:
            continue

        lines.append(text)

        if text.strip().lower() == "ok":
            break

    return lines


def run_probe(port: str, baud: int, timeout: float, settle: float) -> int:
    validate_safe_commands()

    try:
        import serial
    except Exception as exc:
        return fail(
            "pyserial is not available. Install/check project environment first. "
            f"Import error: {exc}"
        )

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = LOG_DIR / f"phase_2_2a_mk4s_readonly_probe_{stamp}.txt"

    transcript: list[str] = []
    transcript.append("PHASE 2.2A REAL HARDWARE READ-ONLY PROBE")
    transcript.append(f"time={datetime.now().isoformat(timespec='seconds')}")
    transcript.append(f"port={port}")
    transcript.append(f"baud={baud}")
    transcript.append("allowed_commands=" + ", ".join(SAFE_READONLY_COMMANDS))
    transcript.append("safety=no movement, no homing, no heating")
    transcript.append("")

    print("=== OPENING SERIAL PORT READ-ONLY ===")
    print(f"port={port}")
    print(f"baud={baud}")
    print("Allowed commands:", ", ".join(SAFE_READONLY_COMMANDS))
    print("No movement commands will be sent.")
    print("")

    try:
        with serial.Serial(port=port, baudrate=baud, timeout=0.25, write_timeout=2) as ser:
            print("Serial opened.")
            print(f"Waiting {settle:.1f}s for printer/USB settle...")
            time.sleep(settle)

            startup_lines = read_available(ser, 2.0)
            if startup_lines:
                transcript.append("=== STARTUP / BUFFERED LINES ===")
                transcript.extend(startup_lines)
                transcript.append("")

            for command in SAFE_READONLY_COMMANDS:
                print(f"Sending readonly command: {command}")
                lines = send_readonly_command(ser, command, timeout)
                transcript.append(f"=== COMMAND {command} ===")
                transcript.extend(lines)
                transcript.append("")

    except Exception as exc:
        transcript.append(f"ERROR: {exc}")
        log_path.write_text("\n".join(transcript), encoding="utf-8")
        return fail(f"hardware readonly probe failed. Transcript saved: {log_path}")

    log_path.write_text("\n".join(transcript), encoding="utf-8")

    print("")
    print("=== READ-ONLY PROBE COMPLETE ===")
    print(f"Transcript saved: {log_path}")
    print("")
    print("=== TRANSCRIPT PREVIEW ===")
    print("\n".join(transcript[-80:]))

    summary = {
        "phase": "2.2A",
        "mode": "real_hardware_readonly",
        "port": port,
        "baud": baud,
        "commands": SAFE_READONLY_COMMANDS,
        "log": str(log_path),
        "safety": "no movement, no homing, no heating",
    }
    print("")
    print("=== JSON SUMMARY ===")
    print(json.dumps(summary, indent=2))

    return 0


def self_test() -> int:
    validate_safe_commands()

    joined = " ".join(SAFE_READONLY_COMMANDS).upper()
    forbidden_hits = []
    for forbidden in FORBIDDEN_PREFIXES:
        pattern = r"\b" + re.escape(forbidden) + r"\b"
        if re.search(pattern, joined):
            forbidden_hits.append(forbidden)

    if forbidden_hits:
        return fail(f"Forbidden command found in readonly command list: {forbidden_hits}")

    print("SELF_TEST_OK")
    print("Readonly commands:", ", ".join(SAFE_READONLY_COMMANDS))
    print("Forbidden motion/heating/homing commands are not present.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--list-ports", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--port", default="")
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--timeout", type=float, default=5.0)
    parser.add_argument("--settle", type=float, default=3.0)
    args = parser.parse_args()

    if args.self_test:
        return self_test()

    if args.list_ports:
        return list_ports()

    if not args.port:
        print("No --port provided.")
        print("Run first:")
        print(r"  .\.venv\Scripts\python.exe tools\phase_2_2a_mk4s_readonly_probe.py --list-ports")
        return 2

    return run_probe(args.port, args.baud, args.timeout, args.settle)


if __name__ == "__main__":
    raise SystemExit(main())
