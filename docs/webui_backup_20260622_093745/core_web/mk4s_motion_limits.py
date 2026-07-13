from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class MK4SMotionLimits:
    machine: str = "Original Prusa MK4S scanner platform"
    machine_family: str = "Prusa-MK4"
    firmware_family: str = "Prusa Buddy / Marlin-compatible G-code"
    project_role: str = "Educational SPM / scanner motion platform"

    x_build_mm: float = 250.0
    y_build_mm: float = 210.0
    z_build_mm: float = 220.0

    x_safe_min_mm: float = 20.0
    x_safe_max_mm: float = 80.0
    y_safe_min_mm: float = 20.0
    y_safe_max_mm: float = 80.0
    safe_center_x_mm: float = 125.0
    safe_center_y_mm: float = 105.0
    safe_parking_z_mm: float = 120.0
    safe_retract_z_min_mm: float = 120.0
    safe_retract_z_max_mm: float = 150.0

    x_steps_per_mm: float = 100.0
    y_steps_per_mm: float = 100.0
    z_steps_per_mm: float = 400.0

    xy_command_resolution_um: float = 10.0
    z_command_resolution_um: float = 2.5

    x_hw_max_speed_mm_s: float = 300.0
    y_hw_max_speed_mm_s: float = 300.0
    z_hw_max_speed_mm_s: float = 40.0

    x_default_max_feedrate_mm_s: float = 300.0
    y_default_max_feedrate_mm_s: float = 300.0
    z_default_max_feedrate_mm_s: float = 40.0

    demo_x_min_mm: float = 20.0
    demo_x_max_mm: float = 80.0
    demo_y_min_mm: float = 20.0
    demo_y_max_mm: float = 80.0

    demo_x_points: int = 64
    demo_y_lines: int = 32

    recommended_scan_speed_min_mm_s: float = 1.0
    recommended_scan_speed_default_mm_s: float = 5.0
    recommended_scan_speed_max_mm_s: float = 10.0

    recommended_travel_speed_mm_s: float = 20.0
    recommended_xy_health_test_speed_mm_s: float = 10.0
    recommended_z_approach_min_mm_s: float = 0.05
    recommended_z_approach_default_mm_s: float = 0.10
    recommended_z_approach_max_mm_s: float = 0.50

    recommended_z_manual_step_default_mm: float = 0.10
    recommended_z_manual_step_expert_mm: float = 0.01
    recommended_z_fine_step_um: float = 10.0
    recommended_z_retract_mm: float = 25.0
    recommended_z_retract_speed_min_mm_s: float = 5.0
    recommended_z_retract_speed_max_mm_s: float = 10.0

    nozzle: str = "High-flow Prusa Nozzle brass CHT 0.4 mm"
    filament_diameter_mm: float = 1.75
    slicer_layer_height_min_mm: float = 0.05
    slicer_layer_height_max_mm: float = 0.30
    loadcell_note: str = (
        "MK4S has a loadcell-based Nextruder, but scanner contact feedback is not verified. "
        "M119 is read-only status only until a feedback channel is validated."
    )


MK4S_LIMITS = MK4SMotionLimits()


def motion_limits_payload() -> dict:
    data = asdict(MK4S_LIMITS)
    data["xy_gcode_resolution_mm"] = 1.0 / MK4S_LIMITS.x_steps_per_mm
    data["z_gcode_resolution_mm"] = 1.0 / MK4S_LIMITS.z_steps_per_mm
    data["xy_hw_max_feedrate_f_mm_min"] = MK4S_LIMITS.x_hw_max_speed_mm_s * 60.0
    data["z_hw_max_feedrate_f_mm_min"] = MK4S_LIMITS.z_hw_max_speed_mm_s * 60.0
    data["safe_scan_envelope"] = {
        "x_min_mm": MK4S_LIMITS.x_safe_min_mm,
        "x_max_mm": MK4S_LIMITS.x_safe_max_mm,
        "y_min_mm": MK4S_LIMITS.y_safe_min_mm,
        "y_max_mm": MK4S_LIMITS.y_safe_max_mm,
    }
    data["safe_center"] = {
        "x_mm": MK4S_LIMITS.safe_center_x_mm,
        "y_mm": MK4S_LIMITS.safe_center_y_mm,
        "parking_z_mm": MK4S_LIMITS.safe_parking_z_mm,
    }
    data["ui_warnings"] = [
        "Motion command resolution is not real AFM/STM surface resolution.",
        MK4S_LIMITS.loadcell_note,
    ]
    return data

def estimate_raster_time_seconds(
    x_min_mm: float,
    x_max_mm: float,
    y_lines: int,
    scan_speed_mm_s: float,
    overhead_per_line_s: float = 0.25,
) -> float:
    if y_lines <= 0:
        raise ValueError("y_lines must be positive")
    if scan_speed_mm_s <= 0:
        raise ValueError("scan_speed_mm_s must be positive")

    line_length_mm = abs(float(x_max_mm) - float(x_min_mm))
    line_time_s = line_length_mm / float(scan_speed_mm_s)
    return y_lines * (line_time_s + float(overhead_per_line_s))


def validate_recommended_scan_speed(speed_mm_s: float) -> tuple[bool, str]:
    speed = float(speed_mm_s)
    lo = MK4S_LIMITS.recommended_scan_speed_min_mm_s
    hi = MK4S_LIMITS.recommended_scan_speed_max_mm_s
    if speed < lo:
        return False, f"Below recommended demo scan speed ({lo} mm/s)."
    if speed > hi:
        return False, f"Above recommended demo scan speed ({hi} mm/s)."
    return True, "Within recommended educational scan speed range."
