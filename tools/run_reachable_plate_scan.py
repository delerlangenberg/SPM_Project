"""Real adaptive survey of the currently probe-reachable MK4S plate.

Coordinates written as ``probe_*`` are sample positions in the MK4S firmware
coordinate system. Coordinates written as ``nozzle_*`` are G-code carriage
coordinates. The MK4S was physically observed to move left as commanded X
increases. Therefore a probe mounted 51 mm physically right of the nozzle has
firmware-coordinate offset dx = -51 mm.
"""

from __future__ import annotations

import csv
import json
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import serial

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

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


PROBE_DX_MM = -51.0
PROBE_DY_MM = 0.0
NOZZLE_X_MIN = 53.0
NOZZLE_X_MAX = 248.0
NOZZLE_Y_MIN = 2.0
NOZZLE_Y_MAX = 208.0
PROBE_X_MIN = NOZZLE_X_MIN + PROBE_DX_MM
PROBE_X_MAX = NOZZLE_X_MAX + PROBE_DX_MM
PROBE_Y_MIN = NOZZLE_Y_MIN + PROBE_DY_MM
PROBE_Y_MAX = NOZZLE_Y_MAX + PROBE_DY_MM
DISCOVERY_Y = 105.0
LOCAL_Z = 19.7
HARD_FLOOR_Z = 16.2
APPROACH_SPEED_MM_S = 0.8
APPROACH_FEED = APPROACH_SPEED_MM_S * 60.0
FINE_Z_STEP_MM = 0.05
EXPECTED_FIRMWARE = "firmware=0.8.5-lcd-rgb-approach"


@dataclass(frozen=True)
class ReachReading:
    sequence: int
    phase: str
    nozzle_x_mm: float
    nozzle_y_mm: float
    probe_x_mm: float
    probe_y_mm: float
    contact: bool
    trigger_z_mm: float | None
    trigger_z_resolution_mm: float | None
    edges: int


def inclusive_positions(start: float, stop: float, pitch: float) -> tuple[float, ...]:
    values: list[float] = []
    value = start
    while value <= stop + 1e-9:
        values.append(round(value, 3))
        value += pitch
    if values[-1] != stop:
        values.append(stop)
    return tuple(values)


def _point_key(x_mm: float, y_mm: float) -> tuple[float, float]:
    return round(x_mm, 3), round(y_mm, 3)


def write_csv(path: Path, readings: list[ReachReading]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "sequence",
                "phase",
                "nozzle_x_mm",
                "nozzle_y_mm",
                "probe_x_mm",
                "probe_y_mm",
                "contact",
                "trigger_z_mm",
                "trigger_z_resolution_mm",
                "edges",
                "measurement_kind",
            ]
        )
        for reading in readings:
            writer.writerow(
                [
                    reading.sequence,
                    reading.phase,
                    f"{reading.nozzle_x_mm:.3f}",
                    f"{reading.nozzle_y_mm:.3f}",
                    f"{reading.probe_x_mm:.3f}",
                    f"{reading.probe_y_mm:.3f}",
                    int(reading.contact),
                    (
                        f"{reading.trigger_z_mm:.3f}"
                        if reading.trigger_z_mm is not None
                        else ""
                    ),
                    (
                        f"{reading.trigger_z_resolution_mm:.3f}"
                        if reading.trigger_z_resolution_mm is not None
                        else ""
                    ),
                    reading.edges,
                    "PHYSICAL",
                ]
            )


def load_csv(path: Path) -> list[ReachReading]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return [
            ReachReading(
                sequence=int(row["sequence"]),
                phase=row["phase"],
                nozzle_x_mm=float(row["nozzle_x_mm"]),
                nozzle_y_mm=float(row["nozzle_y_mm"]),
                probe_x_mm=float(row["probe_x_mm"]),
                probe_y_mm=float(row["probe_y_mm"]),
                contact=row["contact"] == "1",
                trigger_z_mm=(
                    float(row["trigger_z_mm"]) if row["trigger_z_mm"] else None
                ),
                trigger_z_resolution_mm=(
                    float(row["trigger_z_resolution_mm"])
                    if row["trigger_z_resolution_mm"]
                    else None
                ),
                edges=int(row["edges"]),
            )
            for row in csv.DictReader(handle)
        ]


def measure_point(
    printer,
    mega,
    sequence: int,
    phase: str,
    nozzle_x: float,
    nozzle_y: float,
    *,
    fine_z: bool,
) -> ReachReading:
    if not (
        NOZZLE_X_MIN <= nozzle_x <= NOZZLE_X_MAX
        and NOZZLE_Y_MIN <= nozzle_y <= NOZZLE_Y_MAX
    ):
        raise RuntimeError(f"Point outside nozzle envelope X{nozzle_x} Y{nozzle_y}")

    move_z(printer, LOCAL_Z, 300)
    printer_command(printer, f"G1 X{nozzle_x:.3f} Y{nozzle_y:.3f} F2400", 10)
    wait_for_motion(printer, 30)
    mega_command(mega, "RESET")
    mega_command(mega, "STOW")
    mega_command(mega, "CLEAR_TRIGGER")
    mega_command(mega, "DEPLOY")
    mega_command(mega, "CLEAR_TRIGGER")
    baseline = probe_status(mega)
    if baseline["D3_raw"] or baseline["trigger_latched"]:
        raise RuntimeError(f"Point {sequence}: invalid trigger baseline.")

    if fine_z:
        targets = [
            round(17.8 - index * FINE_Z_STEP_MM, 3)
            for index in range(
                1, int(round((17.8 - HARD_FLOOR_Z) / FINE_Z_STEP_MM)) + 1
            )
        ]
        z_resolution = FINE_Z_STEP_MM
    else:
        # Fast empty-field discovery. Each move remains above the same hard
        # floor and the latched trigger is checked at every tier.
        targets = [17.75, 17.0, HARD_FLOOR_Z]
        z_resolution = None

    evidence = baseline
    trigger_z = None
    for target_z in targets:
        move_z(printer, target_z, APPROACH_FEED)
        evidence = probe_status(mega)
        if evidence["trigger_latched"]:
            trigger_z = printer_position(printer)[2]
            break

    mega_command(mega, "STOW")
    move_z(printer, LOCAL_Z, 300)
    return ReachReading(
        sequence=sequence,
        phase=phase,
        nozzle_x_mm=nozzle_x,
        nozzle_y_mm=nozzle_y,
        probe_x_mm=nozzle_x + PROBE_DX_MM,
        probe_y_mm=nozzle_y + PROBE_DY_MM,
        contact=trigger_z is not None,
        trigger_z_mm=trigger_z,
        trigger_z_resolution_mm=z_resolution if trigger_z is not None else None,
        edges=evidence["edges"],
    )


def render_plot(
    path: Path,
    readings: list[ReachReading],
    regions_nozzle: list[tuple[float, float, float]],
) -> None:
    import matplotlib

    matplotlib.use("Agg")
    from matplotlib import pyplot as plt

    contact = [reading for reading in readings if reading.contact]
    no_contact = [reading for reading in readings if not reading.contact]
    figure, axis = plt.subplots(figsize=(11, 8))
    axis.axvspan(
        PROBE_X_MAX,
        250.0,
        color="#d1d5db",
        alpha=0.9,
        label="Current mount: physically left strip inaccessible",
    )
    axis.add_patch(
        plt.Rectangle(
            (PROBE_X_MIN, PROBE_Y_MIN),
            PROBE_X_MAX - PROBE_X_MIN,
            PROBE_Y_MAX - PROBE_Y_MIN,
            fill=False,
            color="#0f766e",
            linewidth=2.0,
            label="Validated reachable envelope",
        )
    )
    if contact:
        fine_contact = [
            reading for reading in contact if reading.trigger_z_resolution_mm is not None
        ]
        coarse_contact = [
            reading for reading in contact if reading.trigger_z_resolution_mm is None
        ]
        if fine_contact:
            image = axis.scatter(
                [reading.probe_x_mm for reading in fine_contact],
                [reading.probe_y_mm for reading in fine_contact],
                c=[reading.trigger_z_mm for reading in fine_contact],
                cmap="viridis",
                s=38,
                edgecolors="white",
                linewidths=0.4,
                label="Fine physical contact",
            )
            figure.colorbar(image, ax=axis, label="Measured trigger Z (mm)")
        if coarse_contact:
            axis.scatter(
                [reading.probe_x_mm for reading in coarse_contact],
                [reading.probe_y_mm for reading in coarse_contact],
                marker="s",
                color="#f59e0b",
                s=32,
                label="Coarse physical contact",
            )
    if no_contact:
        axis.scatter(
            [reading.probe_x_mm for reading in no_contact],
            [reading.probe_y_mm for reading in no_contact],
            marker="x",
            color="#dc2626",
            s=28,
            label="Physical no-contact by Z16.2",
        )
    for index, (first_nozzle_x, last_nozzle_x, center_nozzle_x) in enumerate(
        sorted(regions_nozzle), start=1
    ):
        first_probe_x = first_nozzle_x + PROBE_DX_MM
        last_probe_x = last_nozzle_x + PROBE_DX_MM
        probe_x = center_nozzle_x + PROBE_DX_MM
        probe_y = DISCOVERY_Y + PROBE_DY_MM
        axis.plot(
            [first_probe_x, last_probe_x],
            [probe_y, probe_y],
            color="#111827",
            linewidth=2.2,
        )
        axis.annotate(
            f"Line contact region {index}\n"
            f"X{first_probe_x:.1f}..{last_probe_x:.1f}",
            (probe_x, probe_y),
            xytext=(6, 7),
            textcoords="offset points",
            fontsize=8,
        )
    axis.set(
        title="Current CR Touch Mount — Reachable Plate Survey",
        xlabel="Physical CR Touch / sample X (mm)",
        ylabel="Physical CR Touch / sample Y (mm)",
        xlim=(0.0, 250.0),
        ylim=(0.0, 210.0),
        aspect="equal",
    )
    axis.grid(True, alpha=0.22)
    axis.legend(loc="upper left", fontsize=8)
    figure.tight_layout()
    figure.savefig(path, dpi=170)
    plt.close(figure)


def run(resume_csv: Path | None = None) -> int:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = PROJECT_ROOT / "data" / "crtouch_profiles"
    csv_path = resume_csv or output_dir / f"reachable_plate_{stamp}.csv"
    plot_path = csv_path.with_suffix(".png")
    summary_path = csv_path.with_name(f"{csv_path.stem}_summary.json")
    readings = load_csv(csv_path) if resume_csv else []
    measured = {
        _point_key(reading.nozzle_x_mm, reading.nozzle_y_mm)
        for reading in readings
    }
    sequence = len(readings)

    discovery_config = DiscoveryConfig(
        x_min_mm=NOZZLE_X_MIN,
        x_max_mm=NOZZLE_X_MAX,
        discovery_y_mm=DISCOVERY_Y,
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
                    f"Unsafe start X{x_start} Y{y_start} Z{z_start}; expected Z{LOCAL_Z} or higher."
                )
            identity = " ".join(mega_command(mega, "INFO"))
            if EXPECTED_FIRMWARE not in identity:
                raise RuntimeError("Required Mega approach firmware is not loaded.")
            printer_command(printer, "G90", 5)

            # Fine common-axis discovery finds the two retained spacers without
            # using their prior centers.
            for nozzle_x in discovery_config.coarse_x_positions():
                if _point_key(nozzle_x, DISCOVERY_Y) in measured:
                    continue
                sequence += 1
                reading = measure_point(
                    printer,
                    mega,
                    sequence,
                    "OBJECT_DISCOVERY",
                    nozzle_x,
                    DISCOVERY_Y,
                    fine_z=True,
                )
                readings.append(reading)
                measured.add(_point_key(nozzle_x, DISCOVERY_Y))
                write_csv(csv_path, readings)
                print(
                    f"REACH_POINT_RESULT {sequence} phase=OBJECT_DISCOVERY "
                    f"probe_X={reading.probe_x_mm:.3f} probe_Y={reading.probe_y_mm:.3f} "
                    f"contact={int(reading.contact)} Z={reading.trigger_z_mm}",
                    flush=True,
                )

            discovery_samples = [
                DiscoverySample(
                    reading.nozzle_x_mm, reading.contact, reading.trigger_z_mm
                )
                for reading in readings
                if reading.phase in {"OBJECT_DISCOVERY", "OBJECT_EDGE_REFINEMENT"}
            ]
            for nozzle_x in refinement_x_positions(
                discovery_samples, discovery_config
            ):
                if _point_key(nozzle_x, DISCOVERY_Y) in measured:
                    continue
                sequence += 1
                reading = measure_point(
                    printer,
                    mega,
                    sequence,
                    "OBJECT_EDGE_REFINEMENT",
                    nozzle_x,
                    DISCOVERY_Y,
                    fine_z=True,
                )
                readings.append(reading)
                measured.add(_point_key(nozzle_x, DISCOVERY_Y))
                write_csv(csv_path, readings)
                print(
                    f"REACH_EDGE_RESULT {sequence} nozzle_X={nozzle_x:.3f} "
                    f"probe_X={reading.probe_x_mm:.3f} contact={int(reading.contact)} "
                    f"Z={reading.trigger_z_mm}",
                    flush=True,
                )

            refined_samples = [
                DiscoverySample(
                    reading.nozzle_x_mm, reading.contact, reading.trigger_z_mm
                )
                for reading in readings
                if reading.phase in {"OBJECT_DISCOVERY", "OBJECT_EDGE_REFINEMENT"}
            ]
            components = contact_components(refined_samples, discovery_config)
            if len(components) < 2:
                raise RuntimeError(
                    f"Expected at least two contact regions; detected {len(components)}."
                )
            regions_nozzle = [
                (
                    component.first_contact_x_mm,
                    component.last_contact_x_mm,
                    component.estimated_center_x_mm,
                )
                for component in components
            ]
            print(
                "REACH_CONTACT_REGIONS_FOUND nozzle_regions="
                f"{regions_nozzle} probe_regions="
                f"{[(a + PROBE_DX_MM, b + PROBE_DX_MM, c + PROBE_DX_MM) for a, b, c in regions_nozzle]}",
                flush=True,
            )

            # Survey the rest of the reachable plate at 25 mm pitch. These are
            # physical controls, not interpolated pixels.
            grid = [
                (x_mm, y_mm)
                for y_mm in inclusive_positions(NOZZLE_Y_MIN, NOZZLE_Y_MAX, 25.0)
                for x_mm in inclusive_positions(NOZZLE_X_MIN, NOZZLE_X_MAX, 25.0)
                if _point_key(x_mm, y_mm) not in measured
            ]
            for index, (nozzle_x, nozzle_y) in enumerate(grid, start=1):
                sequence += 1
                reading = measure_point(
                    printer,
                    mega,
                    sequence,
                    "REACHABLE_FIELD_SURVEY",
                    nozzle_x,
                    nozzle_y,
                    fine_z=False,
                )
                readings.append(reading)
                measured.add(_point_key(nozzle_x, nozzle_y))
                write_csv(csv_path, readings)
                if len(readings) >= 3:
                    render_plot(plot_path, readings, regions_nozzle)
                print(
                    f"REACH_FIELD_RESULT {index}/{len(grid)} sequence={sequence} "
                    f"probe_X={reading.probe_x_mm:.3f} probe_Y={reading.probe_y_mm:.3f} "
                    f"contact={int(reading.contact)} Z={reading.trigger_z_mm}",
                    flush=True,
                )
                if index % 35 == 0 and index < len(grid):
                    mega_command(mega, "STOW")
                    move_z(printer, 25.0, 300)
                    print("COOLING_CHECKPOINT seconds=20", flush=True)
                    time.sleep(20)

            full_retract(printer, mega, "REACHABLE_PLATE_SCAN_COMPLETE")
            render_plot(plot_path, readings, regions_nozzle)
            summary = {
                "status": "PASS",
                "mode": "REAL_HARDWARE_ADAPTIVE_REACH_SURVEY",
                "probe_offset_mm": {
                    "dx": PROBE_DX_MM,
                    "dy": PROBE_DY_MM,
                    "status": "PROVISIONAL_OPERATOR_MEASUREMENT",
                },
                "inaccessible_probe_strip_mm": {
                    "firmware_x": [PROBE_X_MAX, 250.0],
                    "physical_description": "leftmost approximately 53 mm",
                },
                "reachable_probe_bounds_mm": {
                    "x": [PROBE_X_MIN, PROBE_X_MAX],
                    "y": [PROBE_Y_MIN, PROBE_Y_MAX],
                },
                "authorized_nozzle_bounds_mm": {
                    "x": [NOZZLE_X_MIN, NOZZLE_X_MAX],
                    "y": [NOZZLE_Y_MIN, NOZZLE_Y_MAX],
                },
                "physical_measurements": len(readings),
                "contacts": sum(reading.contact for reading in readings),
                "no_contacts": sum(not reading.contact for reading in readings),
                "field_survey_pitch_mm": 25.0,
                "object_edge_refinement_pitch_mm": 0.5,
                "fine_z_command_increment_mm": FINE_Z_STEP_MM,
                "approach_speed_mm_s": APPROACH_SPEED_MM_S,
                "detected_line_contact_regions_nozzle_mm": regions_nozzle,
                "detected_line_contact_regions_probe_mm": [
                    [a + PROBE_DX_MM, b + PROBE_DX_MM, c + PROBE_DX_MM]
                    for a, b, c in regions_nozzle
                ],
                "safe_retract_confirmed_z_mm": 120.0,
                "csv": str(csv_path),
                "plot": str(plot_path),
                "measurement_note": (
                    "All CSV rows are physical measurements. Because commanded "
                    "X increases physically left, firmware X197..250 is the "
                    "physically left approximately 53 mm inaccessible strip."
                ),
            }
            summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
            print("REACHABLE_PLATE_SCAN_PASS", json.dumps(summary), flush=True)
            print("REACH_SCAN_CSV", csv_path, flush=True)
            print("REACH_SCAN_PLOT", plot_path, flush=True)
            print("REACH_SCAN_SUMMARY", summary_path, flush=True)
            return 0
        except Exception as exc:
            print("REACHABLE_PLATE_SCAN_FAULT", repr(exc), flush=True)
            try:
                full_retract(printer, mega, "REACHABLE_PLATE_SCAN_FAULT")
            except Exception as retract_exc:
                print("RETRACT_FAULT", repr(retract_exc), flush=True)
            return 2


if __name__ == "__main__":
    resume_arg = (
        Path(sys.argv[2])
        if len(sys.argv) == 3 and sys.argv[1] == "--resume"
        else None
    )
    raise SystemExit(run(resume_arg))
