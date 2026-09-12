"""Device-derived scan geometry and probe-offset validation."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path


CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "spm_mk4s_config.json"


@dataclass(frozen=True)
class ScanConstraints:
    x_probe_min: float
    x_probe_max: float
    y_probe_min: float
    y_probe_max: float
    x_nozzle_min: float
    x_nozzle_max: float
    y_nozzle_min: float
    y_nozzle_max: float
    dx: float
    dy: float
    safety_margin: float
    resolution_min: int
    resolution_max: int
    resolution_default: int
    rotation_min: float
    rotation_max: float
    source: str


def load_scan_constraints(safety_margin: float | None = None) -> ScanConstraints:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    x_min, x_max = map(float, config["motion_limits"]["x"])
    y_min, y_max = map(float, config["motion_limits"]["y"])
    probe = config["probe_offset"]
    ui = config["scan_ui"]
    margin = float(ui["student_safety_margin_mm"] if safety_margin is None else safety_margin)
    dx, dy = float(probe["dx_mm"]), float(probe["dy_mm"])
    # Scan coordinates describe the physical probe/sample location. The probe
    # can only occupy the intersection of the plate envelope and the nozzle
    # carriage envelope translated by the measured probe offset.
    x_probe_min = max(x_min + margin, x_min + dx + margin)
    x_probe_max = min(x_max - margin, x_max + dx - margin)
    y_probe_min = max(y_min + margin, y_min + dy + margin)
    y_probe_max = min(y_max - margin, y_max + dy - margin)
    if x_probe_min >= x_probe_max or y_probe_min >= y_probe_max:
        raise ValueError("Configured probe offset leaves no reachable scan area.")
    return ScanConstraints(
        x_probe_min=x_probe_min,
        x_probe_max=x_probe_max,
        y_probe_min=y_probe_min,
        y_probe_max=y_probe_max,
        x_nozzle_min=max(x_min, x_probe_min - dx),
        x_nozzle_max=min(x_max, x_probe_max - dx),
        y_nozzle_min=max(y_min, y_probe_min - dy),
        y_nozzle_max=min(y_max, y_probe_max - dy),
        dx=dx,
        dy=dy,
        safety_margin=margin,
        resolution_min=int(ui["resolution_min"]),
        resolution_max=int(ui["resolution_max"]),
        resolution_default=int(ui["resolution_default"]),
        rotation_min=float(ui["rotation_min_deg"]),
        rotation_max=float(ui["rotation_max_deg"]),
        source="config/spm_mk4s_config.json (confirmed project profile)",
    )


def validate_scan_rectangle(
    *, center_x: float, center_y: float, width: float, height: float, rotation_deg: float,
    constraints: ScanConstraints,
) -> tuple[bool, str]:
    if width <= 0 or height <= 0:
        return False, "Scan size must be greater than zero."
    angle = math.radians(rotation_deg)
    half_x = (abs(width * math.cos(angle)) + abs(height * math.sin(angle))) / 2.0
    half_y = (abs(width * math.sin(angle)) + abs(height * math.cos(angle))) / 2.0
    bounds = (center_x - half_x, center_x + half_x, center_y - half_y, center_y + half_y)
    if not (
        constraints.x_probe_min <= bounds[0] <= bounds[1] <= constraints.x_probe_max
        and constraints.y_probe_min <= bounds[2] <= bounds[3] <= constraints.y_probe_max
    ):
        return False, "Requested area exceeds probe-reachable region. Adjust X/Y, rotation, or scan size."
    return True, "Scan area is inside the probe-reachable region."
