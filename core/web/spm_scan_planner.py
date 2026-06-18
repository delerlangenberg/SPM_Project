from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

X_COUNTS_PER_MM = 100.0
Y_COUNTS_PER_MM = 100.0
Z_COUNTS_PER_MM = 400.0

X_RESOLUTION_UM = 1000.0 / X_COUNTS_PER_MM
Y_RESOLUTION_UM = 1000.0 / Y_COUNTS_PER_MM
Z_RESOLUTION_UM = 1000.0 / Z_COUNTS_PER_MM

X_MIN_LIMIT = 0.0
X_MAX_LIMIT = 250.0
Y_MIN_LIMIT = 0.0
Y_MAX_LIMIT = 210.0
Z_MIN_LIMIT = 0.0
Z_MAX_LIMIT = 220.0

ScanMode = Literal["x_fast", "y_fast", "four_image"]


@dataclass(frozen=True)
class ScanPlanInput:
    x_min: float
    x_max: float
    y_min: float
    y_max: float
    nx: int
    ny: int
    surface_z: float = 55.0
    clearance_um: float = 500.0
    seconds_per_point: float = 2.0
    mode: ScanMode = "four_image"

def round_axis_mm(value: float, counts_per_mm: float) -> float:
    return round(value * counts_per_mm) / counts_per_mm


def validate_scan_input(inp: ScanPlanInput) -> list[str]:
    errors: list[str] = []

    if not (X_MIN_LIMIT <= inp.x_min < inp.x_max <= X_MAX_LIMIT):
        errors.append("X range is outside Prusa MK4S travel limits.")
    if not (Y_MIN_LIMIT <= inp.y_min < inp.y_max <= Y_MAX_LIMIT):
        errors.append("Y range is outside Prusa MK4S travel limits.")
    if inp.nx < 2:
        errors.append("nx must be at least 2.")
    if inp.ny < 2:
        errors.append("ny must be at least 2.")
    if not (Z_MIN_LIMIT <= inp.surface_z <= Z_MAX_LIMIT):
        errors.append("surface_z is outside Z travel limits.")
    if inp.clearance_um < 0:
        errors.append("clearance_um must not be negative.")
    if inp.seconds_per_point <= 0:
        errors.append("seconds_per_point must be positive.")

    if inp.nx >= 2:
        x_step_um = ((inp.x_max - inp.x_min) / (inp.nx - 1)) * 1000.0
        if x_step_um < X_RESOLUTION_UM:
            errors.append("X pixel pitch is below executable Prusa X resolution.")
    if inp.ny >= 2:
        y_step_um = ((inp.y_max - inp.y_min) / (inp.ny - 1)) * 1000.0
        if y_step_um < Y_RESOLUTION_UM:
            errors.append("Y pixel pitch is below executable Prusa Y resolution.")

    return errors

def build_scan_plan_summary(inp: ScanPlanInput) -> dict:
    errors = validate_scan_input(inp)
    if errors:
        return {"ok": False, "errors": errors}

    x_step_mm = (inp.x_max - inp.x_min) / (inp.nx - 1)
    y_step_mm = (inp.y_max - inp.y_min) / (inp.ny - 1)

    one_trace_points = inp.nx * inp.ny
    if inp.mode == "x_fast":
        total_points = one_trace_points * 2
        image_count = 2
    elif inp.mode == "y_fast":
        total_points = one_trace_points * 2
        image_count = 2
    else:
        total_points = one_trace_points * 4
        image_count = 4

    target_z = inp.surface_z + (inp.clearance_um / 1000.0)
    rounded_target_z = round_axis_mm(target_z, Z_COUNTS_PER_MM)

    return {
        "ok": True,
        "mode": inp.mode,
        "x_range_mm": inp.x_max - inp.x_min,
        "y_range_mm": inp.y_max - inp.y_min,
        "nx": inp.nx,
        "ny": inp.ny,
        "x_step_um": x_step_mm * 1000.0,
        "y_step_um": y_step_mm * 1000.0,
        "x_resolution_um": X_RESOLUTION_UM,
        "y_resolution_um": Y_RESOLUTION_UM,
        "z_resolution_um": Z_RESOLUTION_UM,
        "surface_z_mm": inp.surface_z,
        "target_clearance_um": inp.clearance_um,
        "target_z_mm": target_z,
        "rounded_target_z_mm": rounded_target_z,
        "total_points": total_points,
        "image_count": image_count,
        "estimated_seconds": total_points * inp.seconds_per_point,
    }
