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

def pause(message):
    input("\n" + message + " Press ENTER to continue, or CTRL+C to stop.")

send("M114")
send("M17")
send("G90")

send("G1 Z120 F600", wait=6)
send("M400", wait=2)
send("G1 X50 Y170 F1200", wait=10)
send("M400", wait=2)
send("M114")

pause("Check: tool/nozzle should be above the black foam, safely high.")

for z in [100, 80, 70, 65, 60, 58, 56, 55, 54, 53, 52, 51, 50]:
    pause(f"Next step will move Z to {z}. Stop if close to touching.")
    send(f"G1 Z{z} F120", wait=4)
    send("M400", wait=1)
    send("M114")

send("G1 Z120 F600", wait=6)
send("M400", wait=2)
send("M114")

ser.close()
print("")
print("Closed serial port safely.")
