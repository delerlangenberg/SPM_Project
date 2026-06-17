import csv
import sys
import time
from pathlib import Path
import serial

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from core.system.hardware_initialized_profile import get_motion_controller_settings

OUTPUT = PROJECT_ROOT / "data" / "phase9_x_line_topography_skeleton.csv"
OUTPUT.parent.mkdir(parents=True, exist_ok=True)

settings = get_motion_controller_settings()
ser = serial.Serial(settings["port"], int(settings["baudrate"]), timeout=2)
time.sleep(2)

points = [
    {"x": 115.0, "y": 105.0},
    {"x": 125.0, "y": 105.0},
    {"x": 135.0, "y": 105.0},
]

def send(command, wait=1.0, read_time=8):
    print("")
    print(f">>> {command}")
    ser.write((command + "\n").encode("ascii"))
    time.sleep(wait)
    lines = []
    end = time.time() + read_time
    while time.time() < end:
        line = ser.readline().decode(errors="replace").strip()
        if line:
            print(line)
            lines.append(line)
        if line == "ok":
            break
    return lines

rows = []

send("M114")
send("M17")
send("G90")
send("G1 Z120 F600", wait=6)
send("M400", wait=2)

for index, point in enumerate(points, start=1):
    x = point["x"]
    y = point["y"]

    print(f"\n=== POINT {index}: X={x}, Y={y} ===")

    send(f"G1 X{x} Y{y} F600", wait=5)
    send("M400", wait=1)
    send("M114")

    send("G1 Z56 F60", wait=8)
    send("M400", wait=1)
    position_lines = send("M114")

    rows.append({
        "point": index,
        "x": x,
        "y": y,
        "contact_z_assumed": 56.0,
        "method": "software_step_to_known_foam_contact_z",
        "position_response": " | ".join(position_lines),
    })

    send("G1 Z120 F600", wait=8)
    send("M400", wait=1)
    send("M114")

send("G1 X125 Y105 F600", wait=5)
send("M400", wait=1)
send("M114")

ser.close()

with OUTPUT.open("w", newline="", encoding="utf-8") as file:
    writer = csv.DictWriter(
        file,
        fieldnames=[
            "point",
            "x",
            "y",
            "contact_z_assumed",
            "method",
            "position_response",
        ],
    )
    writer.writeheader()
    writer.writerows(rows)

print("")
print(f"Saved line topography skeleton: {OUTPUT}")
print("Finished safely.")
