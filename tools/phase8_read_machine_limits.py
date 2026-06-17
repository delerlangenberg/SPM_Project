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

def send(command, wait=1.0):
    print("")
    print(f">>> {command}")
    ser.write((command + "\n").encode("ascii"))
    time.sleep(wait)
    end = time.time() + 6
    while time.time() < end:
        line = ser.readline().decode(errors="replace").strip()
        if line:
            print(line)
        if line == "ok":
            break

send("M115")
send("M503")   # report stored firmware settings, read-only
send("M211")   # report software endstops if supported, read-only
send("M114")

ser.close()
print("")
print("Closed serial port safely.")
