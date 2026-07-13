"""SPM raster scan simulation model for the web operator console."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class WebScanProfile:
    x_min: float = 20.0
    x_max: float = 80.0
    y_min: float = 20.0
    y_max: float = 80.0
    x_points: int = 64
    y_points: int = 32
    z_setpoint: float = 0.10
    feedback_gain: float = 1.0
    surface: str = "sphere_on_plane"
    serpentine: bool = True
    scan_direction: str = "X+"

    def validate(self) -> None:
        if self.x_min >= self.x_max:
            raise ValueError("x_min must be smaller than x_max")
        if self.y_min >= self.y_max:
            raise ValueError("y_min must be smaller than y_max")
        if not 2 <= self.x_points <= 500:
            raise ValueError("x_points must be between 2 and 500")
        if not 1 <= self.y_points <= 500:
            raise ValueError("y_points must be between 1 and 500")
        if self.z_setpoint < 0:
            raise ValueError("z_setpoint must be non-negative")
        if self.feedback_gain <= 0:
            raise ValueError("feedback_gain must be positive")
        if self.scan_direction not in {"X+", "X-", "Y+", "Y-"}:
            raise ValueError("scan_direction must be one of X+, X-, Y+, Y-")


def _linspace(start: float, stop: float, points: int) -> list[float]:
    if points == 1:
        return [start]
    step = (stop - start) / (points - 1)
    return [start + i * step for i in range(points)]


def raster_line_coordinates(profile: WebScanProfile, line_index: int) -> tuple[list[tuple[float, float]], str]:
    profile.validate()
    if not 0 <= line_index < profile.y_points:
        raise ValueError("line_index outside scan range")

    x_values = _linspace(profile.x_min, profile.x_max, profile.x_points)
    y_values = _linspace(profile.y_min, profile.y_max, profile.y_points)
    primary_is_x = profile.scan_direction.startswith("X")
    primary_positive = profile.scan_direction.endswith("+")

    if primary_is_x:
        primary = x_values if primary_positive else list(reversed(x_values))
        secondary = y_values[line_index]
        direction = profile.scan_direction
        if profile.serpentine and line_index % 2 == 1:
            primary = list(reversed(primary))
            direction = "X-" if direction == "X+" else "X+"
        return [(x, secondary) for x in primary], direction

    primary = y_values if primary_positive else list(reversed(y_values))
    secondary = x_values[line_index % len(x_values)]
    direction = profile.scan_direction
    if profile.serpentine and line_index % 2 == 1:
        primary = list(reversed(primary))
        direction = "Y-" if direction == "Y+" else "Y+"
    return [(secondary, y) for y in primary], direction


def simulated_surface_height(x: float, y: float, profile: WebScanProfile) -> float:
    cx = (profile.x_min + profile.x_max) / 2.0
    cy = (profile.y_min + profile.y_max) / 2.0
    sx = max(profile.x_max - profile.x_min, 1e-9)
    sy = max(profile.y_max - profile.y_min, 1e-9)

    nx = (x - cx) / (sx / 2.0)
    ny = (y - cy) / (sy / 2.0)

    if profile.surface == "terrace":
        terrace = math.floor((nx + 1.0) * 4.0) * 0.18
        ripple = 0.05 * math.sin(14.0 * nx)
        return terrace + ripple

    if profile.surface == "grid_atoms":
        lattice = math.sin(8.0 * math.pi * (nx + 1.0)) * math.sin(8.0 * math.pi * (ny + 1.0))
        return 0.25 + 0.22 * lattice

    if profile.surface == "bravais_lattice":
        # Oblique Bravais-style lattice: two non-orthogonal basis directions with
        # a small long-range modulation so the topography is not visually flat.
        u = 10.0 * (nx + 0.35 * ny)
        v = 10.0 * (0.22 * nx + ny)
        lattice = (math.cos(2.0 * math.pi * u) + math.cos(2.0 * math.pi * v)) * 0.5
        moire = 0.12 * math.sin(2.0 * math.pi * (1.6 * nx - 1.1 * ny))
        return 0.35 + 0.18 * lattice + moire

    r2 = nx * nx + ny * ny
    if r2 <= 1.0:
        return 1.8 * math.sqrt(1.0 - r2)
    return 0.0


def build_scan_line(profile: WebScanProfile, line_index: int) -> dict[str, Any]:
    profile.validate()

    if not 0 <= line_index < profile.y_points:
        raise ValueError("line_index outside scan range")

    coordinates, direction = raster_line_coordinates(profile, line_index)

    points: list[dict[str, float]] = []

    for point_index, (x, y) in enumerate(coordinates):
        surface_height = simulated_surface_height(x, y, profile)
        z_feedback = profile.z_setpoint + (surface_height * profile.feedback_gain)

        points.append(
            {
                "point_index": point_index,
                "x": round(x, 6),
                "y": round(y, 6),
                "surface_height": round(surface_height, 6),
                "z_feedback": round(z_feedback, 6),
                "feedback_error": 0.0,
            }
        )

    return {
        "line_index": line_index,
        "line_count": profile.y_points,
        "x_points": profile.x_points,
        "direction": direction,
        "z_setpoint": profile.z_setpoint,
        "feedback_gain": profile.feedback_gain,
        "height_source": "simulated_z_feedback_minus_setpoint",
        "points": points,
    }


def profile_from_query(query: dict[str, list[str]]) -> WebScanProfile:
    def get_float(name: str, default: float) -> float:
        try:
            return float(query.get(name, [default])[0])
        except (TypeError, ValueError):
            return default

    def get_int(name: str, default: int) -> int:
        try:
            return int(float(query.get(name, [default])[0]))
        except (TypeError, ValueError):
            return default

    def get_bool(name: str, default: bool) -> bool:
        value = str(query.get(name, [str(default)])[0]).strip().lower()
        return value in {"1", "true", "yes", "on"}

    return WebScanProfile(
        x_min=get_float("x_min", 20.0),
        x_max=get_float("x_max", 80.0),
        y_min=get_float("y_min", 20.0),
        y_max=get_float("y_max", 80.0),
        x_points=get_int("x_points", 64),
        y_points=get_int("y_points", 32),
        z_setpoint=get_float("z_setpoint", 0.10),
        feedback_gain=get_float("feedback_gain", 1.0),
        surface=str(query.get("surface", ["sphere_on_plane"])[0]),
        serpentine=get_bool("serpentine", True),
        scan_direction=str(query.get("scan_direction", ["X+"])[0]),
    )


def scan_profile_payload(profile: WebScanProfile) -> dict[str, Any]:
    profile.validate()
    return {
        "x_min": profile.x_min,
        "x_max": profile.x_max,
        "y_min": profile.y_min,
        "y_max": profile.y_max,
        "x_points": profile.x_points,
        "y_points": profile.y_points,
        "z_setpoint": profile.z_setpoint,
        "feedback_gain": profile.feedback_gain,
        "surface": profile.surface,
        "serpentine": profile.serpentine,
        "scan_direction": profile.scan_direction,
        "scan_principle": "constant_distance_z_feedback_raster",
        "line_sequence": "scan X line, step Y, scan next X line, accumulate topography",
        "execution_allowed": False,
    }
