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
    end = time.time() + 5
    while time.time() < end:
        line = ser.readline().decode(errors="replace").strip()
        if line:
            print(line)
        if line == "ok":
            break

send("M114")
send("M17")              # enable motors, no movement
send("G91")              # relative mode
send("G1 X5 F300", 3.0)  # X +5 mm slowly
send("M400", 2.0)        # wait for movement complete
send("M114")
send("G1 X-5 F300", 3.0) # return X -5 mm
send("M400", 2.0)
send("M114")
send("G90")              # back to absolute mode

ser.close()
print("")
print("Closed serial port safely.")
