"""Zero-motion CR-Touch response tester via Arduino Mega.

Safely exercises probe deploy, contact detection (D3/interrupt latch), and stow
without connecting to the MK4S printer.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import serial
from core.hardware.mega_probe import discover_mega_candidate_ports


def main() -> int:
    ports = discover_mega_candidate_ports()
    if not ports:
        print("ERROR: No Arduino Mega probe controller found.")
        return 1

    port = ports[0]
    print(f"Connecting to Arduino Mega on {port}...")

    ser = serial.Serial(port, 115200, timeout=0.2)
    time.sleep(1.2)
    ser.reset_input_buffer()

    def send_cmd(cmd: str) -> list[str]:
        ser.write((cmd + "\n").encode("ascii"))
        time.sleep(0.12)
        lines = []
        while ser.in_waiting:
            line = ser.readline().decode(errors="replace").strip()
            if line:
                lines.append(line)
        return lines

    # Reset and clear previous triggers
    send_cmd("RESET")
    send_cmd("CLEAR_TRIGGER")
    send_cmd("STOW")

    print("\n[STEP 1] Deploying CR-Touch pin (D8 PWM)...")
    deploy_lines = send_cmd("DEPLOY")
    for l in deploy_lines:
        print("  ", l)

    print("\n[STEP 2] LIVE CONTACT SENSOR READY.")
    print(">>> Touch / push the CR-Touch pin gently with your finger now! <<<")
    print("Monitoring for contact (timeout 15 seconds)...")

    start_time = time.time()
    contact_detected = False

    while time.time() - start_time < 15.0:
        lines = send_cmd("STATUS")
        for line in lines:
            if line.startswith("STATUS"):
                if "D3_raw=1" in line or "trigger_latched=1" in line:
                    elapsed = time.time() - start_time
                    print(f"\n*** [CONTACT DETECTED!] *** (at {elapsed:.2f}s)")
                    print(f"  {line}")
                    contact_detected = True
                    break
        if contact_detected:
            break
        time.sleep(0.08)

    print("\n[STEP 3] Stowing CR-Touch pin...")
    stow_lines = send_cmd("STOW")
    for l in stow_lines:
        print("  ", l)

    send_cmd("CLEAR_TRIGGER")
    ser.close()

    if contact_detected:
        print("\nSUCCESS: CR-Touch trigger response is 100% verified!")
        return 0
    else:
        print("\nNotice: No contact was registered within 15 seconds. Try running again and pushing the pin.")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
