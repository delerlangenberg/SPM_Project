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
    end = time.time() + 8
    while time.time() < end:
        line = ser.readline().decode(errors="replace").strip()
        if line:
            print(line)
        if line == "ok":
            break

def pause(z):
    input(f"\nNext Z={z}. Press ENTER to move, CTRL+C to stop if contact is close.")

send("M114")
send("M17")
send("G90")
send("G1 Z120 F600", wait=6)
send("G1 X125 Y105 F1200", wait=8)
send("M400", wait=2)
send("M114")

for z in [110, 100, 90, 80, 75, 70, 65, 60, 58, 56, 54, 52, 50, 48, 46, 44, 42, 40]:
    pause(z)
    send(f"G1 Z{z} F60", wait=3)
    send("M400", wait=1)
    send("M114")

send("G1 Z120 F600", wait=6)
send("M400", wait=2)
send("M114")

ser.close()
print("")
print("Closed serial port safely.")
