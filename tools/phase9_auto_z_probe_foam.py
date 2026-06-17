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

def send(command, wait=1.0, read_time=10):
    print("")
    print(f">>> {command}")
    ser.write((command + "\n").encode("ascii"))
    time.sleep(wait)
    end = time.time() + read_time
    lines = []
    while time.time() < end:
        line = ser.readline().decode(errors="replace").strip()
        if line:
            print(line)
            lines.append(line)
        if line == "ok":
            break
    return lines

send("M114")
send("M17")
send("G90")
send("G1 Z120 F600", wait=6)
send("G1 X125 Y105 F1200", wait=8)
send("M400", wait=2)
send("M114")

print("")
print("AUTO APPROACH STARTING: G38.2 Z50 F30")
print("If anything looks wrong, press CTRL+C or machine stop.")

send("G38.2 Z50 F30", wait=1, read_time=30)
send("M400", wait=2)
send("M114")

send("G1 Z120 F600", wait=8)
send("M400", wait=2)
send("M114")

ser.close()
print("")
print("Auto approach test finished and retracted.")
