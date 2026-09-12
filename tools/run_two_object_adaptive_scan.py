"""Real CR Touch feedback scan for two separated round objects.

The 100 x 100 mm field is searched on the operator-confirmed common Y axis.
Only measured points are written to CSV. After contact components are found,
the scan concentrates physical samples on each object and its boundary.
"""

from __future__ import annotations

import csv
import json
import math
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import serial

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from core.z_control.crtouch_adaptive_map import adaptive_points
from core.z_control.two_object_discovery import (
    DiscoveryConfig,
    DiscoverySample,
    contact_components,
    refinement_x_positions,
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


FIELD_CENTER_X = 95.5
FIELD_CENTER_Y = 105.0
FIELD_SIZE_MM = 100.0
FIELD_X_MIN = FIELD_CENTER_X - FIELD_SIZE_MM / 2.0
FIELD_X_MAX = FIELD_CENTER_X + FIELD_SIZE_MM / 2.0
FIELD_Y_MIN = FIELD_CENTER_Y - FIELD_SIZE_MM / 2.0
FIELD_Y_MAX = FIELD_CENTER_Y + FIELD_SIZE_MM / 2.0
LOCAL_Z = 19.7
HARD_FLOOR_Z = 16.2
FAST_APPROACH_MM_S = 0.8
FAST_APPROACH_FEED = FAST_APPROACH_MM_S * 60.0
Z_RESOLUTION_MM = 0.05
EXPECTED_FIRMWARE = "firmware=0.8.5-lcd-rgb-approach"


@dataclass(frozen=True)
class ScanReading:
    sequence: int
    phase: str
    x_mm: float
    y_mm: float
    contact: bool
    trigger_z_mm: float | None
    edges: int
    approach_speed_mm_s: float = FAST_APPROACH_MM_S
    z_step_mm: float = Z_RESOLUTION_MM


def _key(x_mm: float, y_mm: float) -> tuple[float, float]:
    return round(x_mm, 3), round(y_mm, 3)


def write_csv(path: Path, readings: list[ScanReading]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "sequence",
                "phase",
                "x_mm",
                "y_mm",
                "contact",
                "trigger_z_mm",
                "edges",
                "approach_speed_mm_s",
                "z_step_mm",
                "measurement_kind",
            ]
        )
        for reading in readings:
            writer.writerow(
                [
                    reading.sequence,
                    reading.phase,
                    f"{reading.x_mm:.3f}",
                    f"{reading.y_mm:.3f}",
                    int(reading.contact),
                    (
                        f"{reading.trigger_z_mm:.3f}"
                        if reading.trigger_z_mm is not None
                        else ""
                    ),
                    reading.edges,
                    f"{reading.approach_speed_mm_s:.3f}",
                    f"{reading.z_step_mm:.3f}",
                    "PHYSICAL",
                ]
            )


def load_csv(path: Path) -> list[ScanReading]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return [
            ScanReading(
                sequence=int(row["sequence"]),
                phase=row["phase"],
                x_mm=float(row["x_mm"]),
                y_mm=float(row["y_mm"]),
                contact=row["contact"] == "1",
                trigger_z_mm=(
                    float(row["trigger_z_mm"]) if row["trigger_z_mm"] else None
                ),
                edges=int(row["edges"]),
                approach_speed_mm_s=float(row["approach_speed_mm_s"]),
                z_step_mm=float(row["z_step_mm"]),
            )
            for row in csv.DictReader(handle)
        ]


def measure_point(printer, mega, sequence: int, phase: str, x_mm: float, y_mm: float) -> ScanReading:
    if not (FIELD_X_MIN <= x_mm <= FIELD_X_MAX and FIELD_Y_MIN <= y_mm <= FIELD_Y_MAX):
        raise RuntimeError(f"Point outside authorized 100 mm field: X{x_mm} Y{y_mm}")

    move_z(printer, LOCAL_Z, 300)
    printer_command(printer, f"G1 X{x_mm:.3f} Y{y_mm:.3f} F2400", 10)
    wait_for_motion(printer, 30)

    mega_command(mega, "RESET")
    mega_command(mega, "STOW")
    mega_command(mega, "CLEAR_TRIGGER")
    mega_command(mega, "DEPLOY")
    mega_command(mega, "CLEAR_TRIGGER")
    baseline = probe_status(mega)
    if baseline["D3_raw"] or baseline["trigger_latched"]:
        raise RuntimeError(
            f"Point {sequence}: unsafe trigger baseline D3={baseline['D3_raw']} "
            f"latched={baseline['trigger_latched']}"
        )

    evidence = baseline
    trigger_z = None
    # The 0.8 mm/s candidate passed the earlier one-iteration sweep. The
    # 0.05 mm command increment remains the deterministic Z resolution.
    for index in range(1, int(round((17.8 - HARD_FLOOR_Z) / Z_RESOLUTION_MM)) + 1):
        target_z = round(17.8 - index * Z_RESOLUTION_MM, 3)
        move_z(printer, target_z, FAST_APPROACH_FEED)
        evidence = probe_status(mega)
        if evidence["trigger_latched"]:
            trigger_z = printer_position(printer)[2]
            break

    mega_command(mega, "STOW")
    move_z(printer, LOCAL_Z, 300)
    return ScanReading(
        sequence=sequence,
        phase=phase,
        x_mm=x_mm,
        y_mm=y_mm,
        contact=trigger_z is not None,
        trigger_z_mm=trigger_z,
        edges=evidence["edges"],
    )


def render_plot(path: Path, readings: list[ScanReading], centers: list[tuple[float, float]]) -> None:
    import matplotlib

    matplotlib.use("Agg")
    from matplotlib import pyplot as plt
    import numpy as np

    contact = [reading for reading in readings if reading.contact]
    no_contact = [reading for reading in readings if not reading.contact]
    figure, axis = plt.subplots(figsize=(10, 8))

    if contact:
        image = axis.scatter(
            [reading.x_mm for reading in contact],
            [reading.y_mm for reading in contact],
            c=[reading.trigger_z_mm for reading in contact],
            cmap="viridis",
            s=36,
            edgecolors="white",
            linewidths=0.45,
            label="Physical contact",
        )
        figure.colorbar(image, ax=axis, label="Measured trigger Z (mm)")
    if no_contact:
        axis.scatter(
            [reading.x_mm for reading in no_contact],
            [reading.y_mm for reading in no_contact],
            marker="x",
            color="#d62728",
            s=34,
            label="Physical no-contact",
        )
    for index, (center_x, center_y) in enumerate(centers, start=1):
        axis.add_patch(
            plt.Circle(
                (center_x, center_y),
                14.6,
                fill=False,
                color="#111111",
                linestyle="--",
                linewidth=1.2,
            )
        )
        axis.annotate(
            f"Object {index}\nX{center_x:.2f}, Y{center_y:.2f}",
            (center_x, center_y),
            xytext=(7, 7),
            textcoords="offset points",
            fontsize=8,
        )

    axis.set(
        title="CR Touch Adaptive Two-Object Scan — 100×100 mm Authorized Field",
        xlabel="MK4S X (mm)",
        ylabel="MK4S Y (mm)",
        xlim=(FIELD_X_MIN, FIELD_X_MAX),
        ylim=(FIELD_Y_MIN, FIELD_Y_MAX),
        aspect="equal",
    )
    axis.grid(True, alpha=0.25)
    axis.legend(loc="lower right")
    figure.tight_layout()
    figure.savefig(path, dpi=170)
    plt.close(figure)


def object_points(centers: list[tuple[float, float]]) -> list[tuple[str, float, float]]:
    """Reuse the validated adaptive pattern around each discovered center."""
    candidates: list[tuple[str, float, float]] = []
    for object_index, (center_x, center_y) in enumerate(centers, start=1):
        for point in adaptive_points(center_x, center_y):
            candidates.append(
                (f"OBJECT_{object_index}_{point.role}", point.x_mm, point.y_mm)
            )
    return candidates


def run(resume_csv: Path | None = None) -> int:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = PROJECT_ROOT / "data" / "crtouch_profiles"
    csv_path = resume_csv or output_dir / f"two_object_100x100_{stamp}.csv"
    plot_path = csv_path.with_suffix(".png")
    summary_path = csv_path.with_name(f"{csv_path.stem}_summary.json")
    readings = load_csv(csv_path)
    measured = {_key(reading.x_mm, reading.y_mm) for reading in readings}

    discovery_config = DiscoveryConfig(
        x_min_mm=FIELD_X_MIN,
        x_max_mm=FIELD_X_MAX,
        discovery_y_mm=FIELD_CENTER_Y,
        coarse_pitch_mm=5.0,
        edge_refinement_pitch_mm=0.5,
        minimum_contact_samples=2,
    )

    with serial.Serial("COM6", 115200, timeout=0.4) as printer, serial.Serial(
        "COM8", 115200, timeout=0.4
    ) as mega:
        time.sleep(2.5)
        printer.reset_input_buffer()
        mega.reset_input_buffer()
        try:
            x_start, y_start, z_start = printer_position(printer)
            if z_start < LOCAL_Z - 0.05:
                raise RuntimeError(
                    f"Unsafe start X{x_start} Y{y_start} Z{z_start}; "
                    f"expected Z{LOCAL_Z} or higher."
                )
            identity = " ".join(mega_command(mega, "INFO"))
            if EXPECTED_FIRMWARE not in identity:
                raise RuntimeError("Required Mega approach firmware is not loaded.")
            printer_command(printer, "G90", 5)

            sequence = len(readings)

            # Phase 1: feedback-driven common-axis discovery across the entire
            # 100 mm width. The requested placement states that both centers
            # share this Y coordinate.
            for x_mm in discovery_config.coarse_x_positions():
                if _key(x_mm, FIELD_CENTER_Y) in measured:
                    continue
                sequence += 1
                print(
                    f"SCAN_POINT_BEGIN {sequence} phase=DISCOVERY "
                    f"X={x_mm:.3f} Y={FIELD_CENTER_Y:.3f}",
                    flush=True,
                )
                reading = measure_point(
                    printer, mega, sequence, "DISCOVERY", x_mm, FIELD_CENTER_Y
                )
                readings.append(reading)
                measured.add(_key(x_mm, FIELD_CENTER_Y))
                write_csv(csv_path, readings)
                print(
                    f"SCAN_POINT_RESULT {sequence} contact={int(reading.contact)} "
                    f"Z={reading.trigger_z_mm}",
                    flush=True,
                )

            discovery_samples = [
                DiscoverySample(
                    reading.x_mm, reading.contact, reading.trigger_z_mm
                )
                for reading in readings
                if reading.phase in {"DISCOVERY", "EDGE_REFINEMENT"}
                and abs(reading.y_mm - FIELD_CENTER_Y) < 0.01
            ]
            for x_mm in refinement_x_positions(
                discovery_samples, discovery_config
            ):
                if _key(x_mm, FIELD_CENTER_Y) in measured:
                    continue
                sequence += 1
                reading = measure_point(
                    printer,
                    mega,
                    sequence,
                    "EDGE_REFINEMENT",
                    x_mm,
                    FIELD_CENTER_Y,
                )
                readings.append(reading)
                measured.add(_key(x_mm, FIELD_CENTER_Y))
                write_csv(csv_path, readings)
                print(
                    f"EDGE_RESULT {sequence} X={x_mm:.3f} "
                    f"contact={int(reading.contact)} Z={reading.trigger_z_mm}",
                    flush=True,
                )

            refined_samples = [
                DiscoverySample(
                    reading.x_mm, reading.contact, reading.trigger_z_mm
                )
                for reading in readings
                if reading.phase in {"DISCOVERY", "EDGE_REFINEMENT"}
                and abs(reading.y_mm - FIELD_CENTER_Y) < 0.01
            ]
            components = contact_components(refined_samples, discovery_config)
            if len(components) != 2:
                raise RuntimeError(
                    f"Expected exactly two separated objects; detected {len(components)}."
                )
            centers = [
                (component.estimated_center_x_mm, FIELD_CENTER_Y)
                for component in components
            ]
            print("TWO_OBJECTS_FOUND", centers, flush=True)

            # Phase 2: concentrate the physical scan on the detected objects.
            # Nearest-neighbour ordering reduces unnecessary XY travel.
            pending = [
                item for item in object_points(centers)
                if _key(item[1], item[2]) not in measured
            ]
            current_x, current_y, _ = printer_position(printer)
            ordered: list[tuple[str, float, float]] = []
            while pending:
                next_item = min(
                    pending,
                    key=lambda item: (item[1] - current_x) ** 2 + (item[2] - current_y) ** 2,
                )
                pending.remove(next_item)
                ordered.append(next_item)
                _, current_x, current_y = next_item

            for index, (phase, x_mm, y_mm) in enumerate(ordered, start=1):
                sequence += 1
                print(
                    f"SCAN_POINT_BEGIN {sequence} adaptive={index}/{len(ordered)} "
                    f"phase={phase} X={x_mm:.3f} Y={y_mm:.3f}",
                    flush=True,
                )
                reading = measure_point(
                    printer, mega, sequence, phase, x_mm, y_mm
                )
                readings.append(reading)
                measured.add(_key(x_mm, y_mm))
                write_csv(csv_path, readings)
                if len(readings) >= 3:
                    render_plot(plot_path, readings, centers)
                print(
                    f"SCAN_POINT_RESULT {sequence} contact={int(reading.contact)} "
                    f"Z={reading.trigger_z_mm}",
                    flush=True,
                )
                if index % 40 == 0 and index < len(ordered):
                    mega_command(mega, "STOW")
                    move_z(printer, 25.0, 300)
                    print("COOLING_CHECKPOINT seconds=20", flush=True)
                    time.sleep(20)

            full_retract(printer, mega, "TWO_OBJECT_SCAN_COMPLETE")
            render_plot(plot_path, readings, centers)
            centers_sorted = sorted(centers)
            center_gap = centers_sorted[1][0] - centers_sorted[0][0]
            edge_gap = center_gap - 29.2
            line_samples = sorted(
                refined_samples, key=lambda sample: sample.x_mm
            )
            left_component_last_contact = max(
                sample.x_mm
                for sample in line_samples
                if sample.contact and sample.x_mm < 105.0
            )
            left_gap_first_no_contact = min(
                sample.x_mm
                for sample in line_samples
                if not sample.contact and sample.x_mm > left_component_last_contact
            )
            right_component_first_contact = min(
                sample.x_mm
                for sample in line_samples
                if sample.contact and sample.x_mm > 105.0
            )
            right_gap_last_no_contact = max(
                sample.x_mm
                for sample in line_samples
                if not sample.contact and sample.x_mm < right_component_first_contact
            )
            gap_min = right_gap_last_no_contact - left_gap_first_no_contact
            gap_max = right_component_first_contact - left_component_last_contact
            summary = {
                "status": "PASS",
                "mode": "REAL_HARDWARE_ADAPTIVE",
                "authorized_field_mm": [100.0, 100.0],
                "field_bounds_mm": {
                    "x": [FIELD_X_MIN, FIELD_X_MAX],
                    "y": [FIELD_Y_MIN, FIELD_Y_MAX],
                },
                "physical_measurements": len(readings),
                "contacts": sum(reading.contact for reading in readings),
                "no_contacts": sum(not reading.contact for reading in readings),
                "approach_speed_mm_s": FAST_APPROACH_MM_S,
                "z_command_resolution_mm": Z_RESOLUTION_MM,
                "detected_centers_mm": centers_sorted,
                "estimated_center_distance_mm": center_gap,
                "estimated_edge_gap_using_known_29_2_mm_diameter": edge_gap,
                "measured_edge_gap_bracket_mm": [gap_min, gap_max],
                "measured_edge_gap_midpoint_mm": (gap_min + gap_max) / 2.0,
                "safe_retract_confirmed_z_mm": 120.0,
                "csv": str(csv_path),
                "plot": str(plot_path),
                "measurement_note": (
                    "CSV rows are physical measurements. Empty regions in the "
                    "100x100 plot are not represented as measured data."
                ),
            }
            summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
            print("TWO_OBJECT_SCAN_PASS", json.dumps(summary), flush=True)
            print("SCAN_CSV", csv_path, flush=True)
            print("SCAN_PLOT", plot_path, flush=True)
            print("SCAN_SUMMARY", summary_path, flush=True)
            return 0
        except Exception as exc:
            print("TWO_OBJECT_SCAN_FAULT", repr(exc), flush=True)
            try:
                full_retract(printer, mega, "TWO_OBJECT_SCAN_FAULT")
            except Exception as retract_exc:
                print("RETRACT_FAULT", repr(retract_exc), flush=True)
            return 2


if __name__ == "__main__":
    resume_arg = Path(sys.argv[2]) if len(sys.argv) == 3 and sys.argv[1] == "--resume" else None
    raise SystemExit(run(resume_arg))
