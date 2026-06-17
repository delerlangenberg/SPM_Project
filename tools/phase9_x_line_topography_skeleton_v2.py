import csv
import sys
import time
from pathlib import Path
import serial
import matplotlib.pyplot as plt

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from core.system.hardware_initialized_profile import get_motion_controller_settings

CSV_OUT = PROJECT_ROOT / "data" / "phase9_x_line_topography_skeleton_v2.csv"
PNG_OUT = PROJECT_ROOT / "data" / "phase9_x_line_topography_skeleton_v2.png"
CSV_OUT.parent.mkdir(parents=True, exist_ok=True)

settings = get_motion_controller_settings()
ser = serial.Serial(settings["port"], int(settings["baudrate"]), timeout=2)
time.sleep(2)

def send(command, wait=0.5, read_time=30):
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

def wait_done():
    send("M400", wait=0.5, read_time=60)

points = [115.0, 125.0, 135.0]
y = 105.0
contact_z = 56.0
safe_z = 120.0

rows = []

send("M114")
send("M17")
send("G90")
send(f"G1 Z{safe_z} F600", read_time=40)
wait_done()

for i, x in enumerate(points, start=1):
    print(f"\n=== POINT {i}: X={x}, Y={y} ===")

    send(f"G1 X{x} Y{y} F600", read_time=40)
    wait_done()
    send("M114")

    send(f"G1 Z{contact_z} F60", read_time=80)
    wait_done()
    pos = send("M114")

    rows.append({
        "point": i,
        "x": x,
        "y": y,
        "contact_z": contact_z,
        "position_response": " | ".join(pos),
    })

    send(f"G1 Z{safe_z} F600", read_time=40)
    wait_done()
    send("M114")

send("G1 X125 Y105 F600", read_time=40)
wait_done()
send("M114")

ser.close()

with CSV_OUT.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["point", "x", "y", "contact_z", "position_response"])
    writer.writeheader()
    writer.writerows(rows)

plt.figure()
plt.plot([r["x"] for r in rows], [r["contact_z"] for r in rows], marker="o")
plt.xlabel("X position (mm)")
plt.ylabel("Contact Z (mm)")
plt.title("Phase 9 X-line Topography Skeleton")
plt.grid(True)
plt.savefig(PNG_OUT, dpi=200, bbox_inches="tight")

print("")
print(f"Saved CSV: {CSV_OUT}")
print(f"Saved PNG: {PNG_OUT}")
print("Finished safely.")
