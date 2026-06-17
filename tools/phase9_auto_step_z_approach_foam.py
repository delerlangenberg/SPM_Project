import sys
import time
from pathlib import Path
import serial

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from core.system.hardware_initialized_profile import get_motion_controller_settings

settings = get_motion_controller_settings()
ser = serial.Serial(settings["port"], int(settings["baudrate"]), timeout=2)
time.sleep(2)

def send(command, wait=1.0, read_time=8):
    print("")
    print(f">>> {command}")
    ser.write((command + "\n").encode("ascii"))
    time.sleep(wait)
    end = time.time() + read_time
    while time.time() < end:
        line = ser.readline().decode(errors="replace").strip()
        if line:
            print(line)
        if line == "ok":
            break

send("M114")
send("M17")
send("G90")
send("G1 Z120 F600", wait=6)
send("G1 X125 Y105 F1200", wait=8)
send("M400", wait=2)
send("M114")

print("")
print("AUTO STEP APPROACH START")
print("Target stop: Z=56 based on manual foam contact reference")

for z in list(range(110, 60, -10)) + [60, 59, 58, 57, 56]:
    print(f"\nAUTO STEP: moving to Z={z}")
    send(f"G1 Z{z} F60", wait=3)
    send("M400", wait=1)
    send("M114")

print("")
print("Reached software stop Z=56. Retracting.")
send("G1 Z120 F600", wait=8)
send("M400", wait=2)
send("M114")

ser.close()
print("")
print("Software auto-step approach finished and retracted.")
