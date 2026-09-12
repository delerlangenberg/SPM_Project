"""Fail-closed adaptive raised-object discovery in the verified envelope."""

from __future__ import annotations

import csv
import argparse
import json
import math
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

import serial

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from tools.run_crtouch_magnet_profile import (
    mega_command,
    printer_command,
    printer_position,
    probe_status,
    wait_for_motion,
)
from core.hardware.stage2_stage_map import stage_map_from_mount_profile

def load_active_geometry() -> dict[str, float]:
    payload = json.loads(
        (PROJECT_ROOT / "config" / "crtouch_mount_profiles.json").read_text(
            encoding="utf-8"
        )
    )
    name = str(payload["active_profile"])
    profile = payload["profiles"][name]
    if name != "center_crtouch_nozzle_removed" or not profile.get("enabled"):
        raise RuntimeError("Centered Stage 2 mount profile is not commissioned.")
    envelope = profile["native_scan_envelope_mm"]
    return {
        "x_min": float(envelope["x_min"]),
        "x_max": float(envelope["x_max"]),
        "y_min": float(envelope["y_min"]),
        "y_max": float(envelope["y_max"]),
        "safe_z": float(profile["safe_travel_z_mm"]),
        "bare_z": float(profile["local_bare_stage_trigger_z_mm"]),
    }


GEOMETRY = load_active_geometry()
X_MIN, X_MAX = GEOMETRY["x_min"], GEOMETRY["x_max"]
Y_MIN, Y_MAX = GEOMETRY["y_min"], GEOMETRY["y_max"]
SAFE_Z = GEOMETRY["safe_z"]
BARE_STAGE_Z = GEOMETRY["bare_z"]
# Search for the previously validated ~10.8 mm raised objects while remaining
# well above the mapped bare-stage range. Unknown-surface scanning uses a
# separate adaptive approach workflow.
SEARCH_Z = tuple(BARE_STAGE_Z + offset for offset in (12.0, 11.5, 11.0, 10.5, 10.0, 9.5))
_MOUNT_PAYLOAD = json.loads(
    (PROJECT_ROOT / "config" / "crtouch_mount_profiles.json").read_text(
        encoding="utf-8"
    )
)
STAGE_MAP = stage_map_from_mount_profile(
    _MOUNT_PAYLOAD["profiles"][_MOUNT_PAYLOAD["active_profile"]]
)
COARSE_PITCH = 20.0
LOCAL_RADIUS = 17.5
EXPECTED_FIRMWARE = "firmware=0.8.5-lcd-rgb-approach"
RESOLUTION_PROFILES = {
    "quick": {"coarse_pitch_mm": 20.0, "focused_pitch_mm": 5.0},
    "high": {"coarse_pitch_mm": 20.0, "focused_pitch_mm": 2.5},
    "research": {"coarse_pitch_mm": 15.0, "focused_pitch_mm": 1.0},
}
MAX_FOCUSED_OBJECTS = 12


@dataclass(frozen=True)
class Reading:
    sequence: int
    phase: str
    native_x_mm: float
    native_y_mm: float
    map_x_mm: float
    map_y_mm: float
    contact: bool
    trigger_z_mm: float | None
    stage_reference_z_mm: float
    height_above_stage_mm: float | None
    edges: int


def axis_values(start: float, stop: float, pitch: float) -> list[float]:
    values: list[float] = []
    value = start
    while value <= stop + 1e-9:
        values.append(round(value, 3))
        value += pitch
    if abs(values[-1] - stop) > 1e-9:
        values.append(stop)
    return values


def map_xy(native_x: float, native_y: float) -> tuple[float, float]:
    return native_x - X_MIN, Y_MAX - native_y


def move_z(printer, target: float, feed: float = 600.0) -> None:
    printer_command(printer, f"G1 Z{target:.3f} F{feed:.0f}", 8)
    wait_for_motion(printer, 12)


def measure(printer, mega, sequence: int, phase: str, x: float, y: float) -> Reading:
    if not (X_MIN <= x <= X_MAX and Y_MIN <= y <= Y_MAX):
        raise RuntimeError(f"Point outside verified envelope: X{x} Y{y}")
    move_z(printer, SAFE_Z)
    printer_command(printer, f"G1 X{x:.3f} Y{y:.3f} F3000", 10)
    wait_for_motion(printer, 20)
    mega_command(mega, "RESET")
    mega_command(mega, "STOW")
    mega_command(mega, "CLEAR_TRIGGER")
    mega_command(mega, "DEPLOY")
    mega_command(mega, "CLEAR_TRIGGER")
    status = probe_status(mega)
    if status["D3_raw"] or status["trigger_latched"]:
        raise RuntimeError(f"Unsafe trigger baseline at X{x} Y{y}: {status}")

    trigger_z = None
    for target in SEARCH_Z:
        move_z(printer, target, 240.0)
        status = probe_status(mega)
        if status["trigger_latched"]:
            trigger_z = printer_position(printer)[2]
            break

    mega_command(mega, "STOW")
    move_z(printer, SAFE_Z)
    mx, my = map_xy(x, y)
    stage_reference = STAGE_MAP.reference_z(x, y)
    return Reading(
        sequence,
        phase,
        x,
        y,
        mx,
        my,
        trigger_z is not None,
        trigger_z,
        stage_reference,
        (
            STAGE_MAP.corrected_height(x, y, trigger_z)
            if trigger_z is not None
            else None
        ),
        status["edges"],
    )


def write_csv(path: Path, readings: list[Reading]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(asdict(readings[0]).keys()))
        writer.writeheader()
        writer.writerows(asdict(item) for item in readings)


def separated_contact_centers(
    points: list[tuple[float, float]],
    pitch_mm: float,
) -> list[tuple[float, float]]:
    """Return centers of spatially separated coarse-contact components."""

    if not points:
        raise RuntimeError("The overview found no raised-object contacts.")
    remaining = set(points)
    components: list[list[tuple[float, float]]] = []
    adjacency = pitch_mm * 1.45
    while remaining:
        pending = [remaining.pop()]
        component: list[tuple[float, float]] = []
        while pending:
            point = pending.pop()
            component.append(point)
            neighbors = {
                candidate
                for candidate in remaining
                if math.dist(point, candidate) <= adjacency
            }
            remaining.difference_update(neighbors)
            pending.extend(neighbors)
        components.append(component)
    if len(components) > MAX_FOCUSED_OBJECTS:
        raise RuntimeError(
            f"Overview found {len(components)} separated regions; "
            f"safe focused limit is {MAX_FOCUSED_OBJECTS}."
        )
    return sorted(
        (
            sum(x for x, _ in component) / len(component),
            sum(y for _, y in component) / len(component),
        )
        for component in components
    )


def render(path: Path, readings: list[Reading], centers: list[tuple[float, float]]) -> None:
    import matplotlib
    matplotlib.use("Agg")
    from matplotlib import pyplot as plt

    fig, axis = plt.subplots(figsize=(9, 9))
    for contact, marker, color, label in (
        (False, "x", "#9ca3af", "No contact"),
        (True, "o", "#16a34a", "CR Touch contact"),
    ):
        rows = [row for row in readings if row.contact is contact]
        if rows:
            axis.scatter(
                [row.map_x_mm for row in rows],
                [row.map_y_mm for row in rows],
                marker=marker, color=color, s=32, label=label,
            )
    for index, (x, y) in enumerate(centers, 1):
        mx, my = map_xy(x, y)
        axis.add_patch(plt.Circle((mx, my), 14.6, fill=False, color="#111827", lw=1.5))
        axis.annotate(f"Object {index}\n({mx:.1f}, {my:.1f}) mm", (mx, my))
    axis.set(
        title="Verified-envelope CR Touch adaptive object map",
        xlabel="CR Touch map X: left → right (mm)",
        ylabel="CR Touch map Y: back → front (mm)",
        xlim=(0, X_MAX - X_MIN),
        ylim=(0, Y_MAX - Y_MIN),
        aspect="equal",
    )
    axis.grid(alpha=0.25)
    axis.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def run(resolution: str = "high") -> int:
    if resolution not in RESOLUTION_PROFILES:
        raise ValueError(f"Unknown resolution profile: {resolution}")
    profile = RESOLUTION_PROFILES[resolution]
    coarse_pitch = float(profile["coarse_pitch_mm"])
    local_pitch = float(profile["focused_pitch_mm"])
    lock = json.loads((PROJECT_ROOT / "config" / "crtouch_hardware_lockout.json").read_text())
    if lock.get("active"):
        raise RuntimeError("CR Touch hardware lockout is active.")
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = PROJECT_ROOT / "data" / "crtouch_profiles"
    csv_path = out / f"verified_two_magnet_map_{stamp}.csv"
    png_path = csv_path.with_suffix(".png")
    summary_path = csv_path.with_name(csv_path.stem + "_summary.json")
    readings: list[Reading] = []

    with serial.Serial("COM6", 115200, timeout=0.4) as printer, serial.Serial(
        "COM8", 115200, timeout=0.4
    ) as mega:
        time.sleep(2.5)
        printer.reset_input_buffer()
        mega.reset_input_buffer()
        try:
            position = printer_position(printer)
            if position[2] < SAFE_Z - 0.05:
                raise RuntimeError(f"Unsafe starting Z: {position}")
            identity = " ".join(mega_command(mega, "INFO"))
            if EXPECTED_FIRMWARE not in identity:
                raise RuntimeError("Required Mega firmware is not loaded.")
            printer_command(printer, "G90", 5)

            xs = axis_values(X_MIN, X_MAX, coarse_pitch)
            ys = axis_values(Y_MIN, Y_MAX, coarse_pitch)
            points: list[tuple[float, float]] = []
            for row, y in enumerate(reversed(ys)):
                row_x = xs if row % 2 == 0 else list(reversed(xs))
                points.extend((x, y) for x in row_x)

            for index, (x, y) in enumerate(points, 1):
                reading = measure(printer, mega, len(readings) + 1, "COARSE", x, y)
                readings.append(reading)
                write_csv(csv_path, readings)
                print(
                    f"COARSE {index}/{len(points)} X={x:.1f} Y={y:.1f} "
                    f"contact={int(reading.contact)}",
                    flush=True,
                )

            coarse_contacts = [
                (row.native_x_mm, row.native_y_mm)
                for row in readings
                if row.phase == "COARSE" and row.contact
            ]
            seeds = separated_contact_centers(coarse_contacts, coarse_pitch)
            print(
                f"COARSE_OBJECTS count={len(seeds)} centers={seeds}",
                flush=True,
            )

            measured = {(round(r.native_x_mm, 3), round(r.native_y_mm, 3)) for r in readings}
            for object_index, (cx, cy) in enumerate(seeds, 1):
                local_x = axis_values(
                    max(X_MIN, cx - LOCAL_RADIUS), min(X_MAX, cx + LOCAL_RADIUS), local_pitch
                )
                local_y = axis_values(
                    max(Y_MIN, cy - LOCAL_RADIUS), min(Y_MAX, cy + LOCAL_RADIUS), local_pitch
                )
                local_points = [
                    (x, y)
                    for row, y in enumerate(local_y)
                    for x in (local_x if row % 2 == 0 else list(reversed(local_x)))
                    if (round(x, 3), round(y, 3)) not in measured
                ]
                for index, (x, y) in enumerate(local_points, 1):
                    reading = measure(
                        printer, mega, len(readings) + 1, f"OBJECT_{object_index}", x, y
                    )
                    readings.append(reading)
                    measured.add((round(x, 3), round(y, 3)))
                    write_csv(csv_path, readings)
                    print(
                        f"MAP object={object_index} {index}/{len(local_points)} "
                        f"contact={int(reading.contact)}",
                        flush=True,
                    )

            centers: list[tuple[float, float]] = []
            for object_index, seed in enumerate(seeds, 1):
                contacts = [
                    (row.native_x_mm, row.native_y_mm)
                    for row in readings
                    if row.phase == f"OBJECT_{object_index}" and row.contact
                ]
                if not contacts:
                    centers.append(seed)
                else:
                    centers.append(
                        (
                            (min(x for x, _ in contacts) + max(x for x, _ in contacts)) / 2,
                            (min(y for _, y in contacts) + max(y for _, y in contacts)) / 2,
                        )
                    )
            centers = sorted(centers)
            render(png_path, readings, centers)
            summary = {
                "status": "PASS",
                "scan_envelope_native_mm": {"x": [X_MIN, X_MAX], "y": [Y_MIN, Y_MAX]},
                "safe_z_mm": SAFE_Z,
                "bare_stage_trigger_z_mm": BARE_STAGE_Z,
                "height_correction": "bilinear_four_corner_stage_map",
                "height_column": "height_above_stage_mm",
                "resolution_profile": resolution,
                "coarse_pitch_mm": coarse_pitch,
                "focused_pitch_mm": local_pitch,
                "readings": len(readings),
                "contacts": sum(row.contact for row in readings),
                "detected_object_count": len(centers),
                "detected_centers_native_mm": centers,
                "detected_centers_map_mm": [map_xy(*center) for center in centers],
                "csv": str(csv_path),
                "plot": str(png_path),
            }
            summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
            move_z(printer, SAFE_Z)
            mega_command(mega, "STOW")
            print("ADAPTIVE_OBJECT_MAP_PASS", json.dumps(summary), flush=True)
            return 0
        except Exception:
            try:
                move_z(printer, SAFE_Z)
                mega_command(mega, "STOW")
            finally:
                raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--resolution",
        choices=tuple(RESOLUTION_PROFILES),
        default="high",
    )
    raise SystemExit(run(parser.parse_args().resolution))
