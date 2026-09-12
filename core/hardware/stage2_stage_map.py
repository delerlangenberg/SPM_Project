"""Stage 2 bare-stage background interpolation for CR Touch height data."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class Stage2StageMap:
    x_min: float
    x_max: float
    y_min: float
    y_max: float
    front_left_z: float
    front_right_z: float
    back_left_z: float
    back_right_z: float

    def reference_z(self, x_mm: float, y_mm: float) -> float:
        """Return bilinear bare-stage trigger Z inside the commissioned field."""

        if not (self.x_min <= x_mm <= self.x_max):
            raise ValueError(f"X{x_mm} is outside the commissioned stage map.")
        if not (self.y_min <= y_mm <= self.y_max):
            raise ValueError(f"Y{y_mm} is outside the commissioned stage map.")
        tx = (x_mm - self.x_min) / (self.x_max - self.x_min)
        ty = (y_mm - self.y_min) / (self.y_max - self.y_min)
        front = self.front_left_z + tx * (
            self.front_right_z - self.front_left_z
        )
        back = self.back_left_z + tx * (
            self.back_right_z - self.back_left_z
        )
        return front + ty * (back - front)

    def corrected_height(self, x_mm: float, y_mm: float, trigger_z_mm: float) -> float:
        return trigger_z_mm - self.reference_z(x_mm, y_mm)


def stage_map_from_mount_profile(profile: Mapping[str, Any]) -> Stage2StageMap:
    envelope = profile["native_scan_envelope_mm"]
    rows = {
        str(row["name"]): float(row["trigger_z_mm"])
        for row in profile["commissioning_evidence"]["stage_map"]
    }
    required = {"front_left", "front_right", "back_left", "back_right"}
    missing = sorted(required - rows.keys())
    if missing:
        raise ValueError(f"Stage map is missing corners: {', '.join(missing)}")
    return Stage2StageMap(
        x_min=float(envelope["x_min"]),
        x_max=float(envelope["x_max"]),
        y_min=float(envelope["y_min"]),
        y_max=float(envelope["y_max"]),
        front_left_z=rows["front_left"],
        front_right_z=rows["front_right"],
        back_left_z=rows["back_left"],
        back_right_z=rows["back_right"],
    )
