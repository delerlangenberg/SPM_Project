from __future__ import annotations

import json
import argparse
import sys
import time
from datetime import datetime
from pathlib import Path

import serial

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from core.z_control.crtouch_adaptive_map import (
    MapReading,
    adaptive_points,
    load_map_csv,
    render_map,
    write_map_csv,
)
from tools.run_crtouch_magnet_profile import (
    full_retract,
    mega_command,
    move_z,
    printer_command,
    printer_position,
    probe_status,
    wait_for_motion,
)


CENTER_X = 125.5
CENTER_Y = 105.0
LOCAL_Z = 19.7
HARD_FLOOR_Z = 16.2


def ordered_points():
    points = list(adaptive_points(CENTER_X, CENTER_Y))
    ordered = [points.pop(0)]
    while points:
        current = ordered[-1]
        next_point = min(
            points,
            key=lambda point: (
                (point.x_mm - current.x_mm) ** 2
                + (point.y_mm - current.y_mm) ** 2
            ),
        )
        points.remove(next_point)
        ordered.append(next_point)
    return ordered


def measure_point(printer, mega, point) -> MapReading:
    move_z(printer, LOCAL_Z, 240)
    printer_command(printer, f"G1 X{point.x_mm:.3f} Y{point.y_mm:.3f} F1800", 10)
    wait_for_motion(printer, 30)
    mega_command(mega, "RESET")
    mega_command(mega, "STOW")
    mega_command(mega, "CLEAR_TRIGGER")
    mega_command(mega, "DEPLOY")
    mega_command(mega, "CLEAR_TRIGGER")
    baseline = probe_status(mega)
    if baseline["D3_raw"] or baseline["trigger_latched"]:
        raise RuntimeError(f"Point {point.index}: invalid trigger baseline.")

    evidence = baseline
    trigger_z = None
    for target_z in (17.8, 17.6, 17.4, 17.2, 17.0, 16.8, 16.6, 16.4, 16.2):
        move_z(printer, target_z, 24)
        evidence = probe_status(mega)
        if evidence["trigger_latched"]:
            trigger_z = printer_position(printer)[2]
            break

    mega_command(mega, "STOW")
    move_z(printer, LOCAL_Z, 240)
    return MapReading(
        point=point,
        contact=trigger_z is not None,
        trigger_z_mm=trigger_z,
        edges=evidence["edges"],
    )


def run(resume_csv: Path | None = None) -> int:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = PROJECT_ROOT / "data" / "crtouch_profiles"
    csv_path = resume_csv or output_dir / f"magnet_adaptive_2d_{stamp}.csv"
    plot_path = csv_path.with_suffix(".png")
    summary_path = csv_path.with_name(f"{csv_path.stem}_summary.json")
    readings = load_map_csv(csv_path) if resume_csv else []
    measured_xy = {
        (round(reading.point.x_mm, 3), round(reading.point.y_mm, 3))
        for reading in readings
    }
    points = [
        point
        for point in ordered_points()
        if (round(point.x_mm, 3), round(point.y_mm, 3)) not in measured_xy
    ]

    with serial.Serial("COM6", 115200, timeout=0.4) as printer, serial.Serial(
        "COM8", 115200, timeout=0.4
    ) as mega:
        time.sleep(2.5)
        printer.reset_input_buffer()
        mega.reset_input_buffer()
        try:
            _, _, z = printer_position(printer)
            if z < LOCAL_Z - 0.05:
                raise RuntimeError(f"Unsafe start Z{z}; expected Z{LOCAL_Z} or higher.")
            identity = " ".join(mega_command(mega, "INFO"))
            if "firmware=0.8.5-lcd-rgb-approach" not in identity:
                raise RuntimeError("Required Mega approach firmware is not loaded.")
            printer_command(printer, "G90", 5)

            for sequence, point in enumerate(points, start=1):
                print(
                    f"MAP_POINT_BEGIN {sequence}/{len(points)} source={point.index} "
                    f"role={point.role} X={point.x_mm:.3f} Y={point.y_mm:.3f}",
                    flush=True,
                )
                reading = measure_point(printer, mega, point)
                readings.append(reading)
                write_map_csv(csv_path, readings)
                if len(readings) >= 3:
                    render_map(plot_path, readings, CENTER_X, CENTER_Y)
                print(
                    f"MAP_POINT_RESULT {sequence}/{len(points)} "
                    f"contact={int(reading.contact)} Z={reading.trigger_z_mm} "
                    f"edges={reading.edges}",
                    flush=True,
                )
                if sequence % 30 == 0 and sequence < len(points):
                    mega_command(mega, "STOW")
                    move_z(printer, 25.0, 300)
                    print("COOLING_CHECKPOINT seconds=20", flush=True)
                    time.sleep(20)

            full_retract(printer, mega, "ADAPTIVE_MAP_COMPLETE")
            render_map(plot_path, readings, CENTER_X, CENTER_Y)
            summary_path.write_text(
                json.dumps(
                    {
                        "status": "PASS",
                        "field_mm": [40, 40],
                        "projection_pixels": [40, 40],
                        "physical_measurements": len(readings),
                        "resumed_from_measurements": len(measured_xy),
                        "contacts": sum(reading.contact for reading in readings),
                        "no_contacts": sum(not reading.contact for reading in readings),
                        "center_x_mm": CENTER_X,
                        "center_y_mm": CENTER_Y,
                        "csv": str(csv_path),
                        "plot": str(plot_path),
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )
            print("ADAPTIVE_MAP_PASS", summary_path, flush=True)
            print("MAP_CSV", csv_path, flush=True)
            print("MAP_PLOT", plot_path, flush=True)
            return 0
        except Exception as exc:
            print("ADAPTIVE_MAP_FAULT", repr(exc), flush=True)
            try:
                full_retract(printer, mega, "ADAPTIVE_MAP_FAULT")
            except Exception as retract_exc:
                print("RETRACT_FAULT", repr(retract_exc), flush=True)
            return 2


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--resume", type=Path)
    arguments = parser.parse_args()
    raise SystemExit(run(arguments.resume))
