import sys
import time
from pathlib import Path

import serial

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from core.system.hardware_initialized_profile import get_motion_controller_settings

settings = get_motion_controller_settings()
port = settings["port"]
baudrate = int(settings["baudrate"])

print(f"Opening {port} at {baudrate}...")
ser = serial.Serial(port, baudrate, timeout=2)
time.sleep(2)

def send(command):
    print("")
    print(f">>> {command}")
    ser.write((command + "\n").encode("ascii"))
    time.sleep(1)

    end = time.time() + 3
    while time.time() < end:
        line = ser.readline().decode(errors="replace").strip()
        if line:
            print(line)
        if line == "ok":
            break

send("M114")
send("M119")
send("M105")

ser.close()
print("")
print("Closed serial port safely.")
