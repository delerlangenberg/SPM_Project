import csv
import sys
import time
from pathlib import Path

import matplotlib.pyplot as plt
import serial

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from core.system.hardware_initialized_profile import get_motion_controller_settings

CSV_OUT = PROJECT_ROOT / "data" / "phase9_xy_3x3_topography_skeleton.csv"
PNG_OUT = PROJECT_ROOT / "data" / "phase9_xy_3x3_topography_skeleton.png"
CSV_OUT.parent.mkdir(parents=True, exist_ok=True)

settings = get_motion_controller_settings()
ser = serial.Serial(settings["port"], int(settings["baudrate"]), timeout=2)
time.sleep(2)

x_points = [115.0, 125.0, 135.0]
y_points = [95.0, 105.0, 115.0]

safe_z = 120.0
contact_z = 56.0

def read_until_ok(read_time=90):
    lines = []
    end = time.time() + read_time
    while time.time() < end:
        line = ser.readline().decode(errors="replace").strip()
        if line:
            print(line)
            lines.append(line)
        if line == "ok":
            return lines
    raise TimeoutError("No ok received from controller")

def send(command, wait=0.5, read_time=90):
    print("")
    print(f">>> {command}")
    ser.reset_input_buffer()
    ser.write((command + "\n").encode("ascii"))
    time.sleep(wait)
    return read_until_ok(read_time)

def move_and_wait(command, wait=0.5, read_time=90):
    send(command, wait=wait, read_time=read_time)
    send("M400", wait=0.5, read_time=read_time)

rows = []

send("M114")
send("M17")
send("G90")
move_and_wait(f"G1 Z{safe_z} F600", read_time=60)

point_index = 0

for y in y_points:
    for x in x_points:
        point_index += 1
        print(f"\n=== POINT {point_index}: X={x}, Y={y} ===")

        move_and_wait(f"G1 X{x} Y{y} F600", read_time=60)
        send("M114")

        move_and_wait(f"G1 Z{contact_z} F60", read_time=120)
        position_lines = send("M114")

        rows.append({
            "point": point_index,
            "x": x,
            "y": y,
            "contact_z": contact_z,
            "method": "fixed_known_foam_contact_z_skeleton",
            "position_response": " | ".join(position_lines),
        })

        move_and_wait(f"G1 Z{safe_z} F600", read_time=60)
        send("M114")

move_and_wait("G1 X125 Y105 F600", read_time=60)
send("M114")

ser.close()

with CSV_OUT.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=["point", "x", "y", "contact_z", "method", "position_response"],
    )
    writer.writeheader()
    writer.writerows(rows)

z_grid = []
for y in y_points:
    z_grid.append([
        next(r["contact_z"] for r in rows if r["x"] == x and r["y"] == y)
        for x in x_points
    ])

plt.figure()
plt.imshow(
    z_grid,
    origin="lower",
    extent=[min(x_points), max(x_points), min(y_points), max(y_points)],
    aspect="auto",
)
plt.colorbar(label="Contact Z (mm)")
plt.xlabel("X position (mm)")
plt.ylabel("Y position (mm)")
plt.title("Phase 9 XY 3x3 Topography Skeleton")
plt.savefig(PNG_OUT, dpi=200, bbox_inches="tight")

print("")
print(f"Saved CSV: {CSV_OUT}")
print(f"Saved PNG: {PNG_OUT}")
print("Finished safely.")
