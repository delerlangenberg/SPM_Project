"""Virtual XYZ scanner motion with bounded speed and optional artifacts."""

from __future__ import annotations

import math
import random
from typing import Callable


class ScannerController:
    def __init__(
        self,
        *,
        max_speed: float = 10.0,
        acceleration: float = 20.0,
        noise_level: float = 0.0005,
        random_source: Callable[[float, float], float] | None = None,
    ) -> None:
        if max_speed <= 0 or acceleration <= 0 or noise_level < 0:
            raise ValueError("invalid scanner dynamics")
        self.position = {"x": 0.0, "y": 0.0, "z": 0.0}
        self.max_speed = float(max_speed)
        self.acceleration = float(acceleration)
        self.noise_level = float(noise_level)
        self.current_speed = {"x": 0.0, "y": 0.0, "z": 0.0}
        self._gauss = random_source or random.gauss

    def move_to(self, target_x: float, target_y: float, target_z: float, dt: float) -> dict[str, float]:
        if dt <= 0:
            raise ValueError("dt must be positive")
        targets = {"x": float(target_x), "y": float(target_y), "z": float(target_z)}
        for axis in ("x", "y", "z"):
            remaining = targets[axis] - self.position[axis]
            desired_speed = min(self.max_speed, abs(remaining) / dt)
            speed_delta = max(-self.acceleration * dt, min(self.acceleration * dt, desired_speed - self.current_speed[axis]))
            self.current_speed[axis] = max(0.0, min(self.max_speed, self.current_speed[axis] + speed_delta))
            step = math.copysign(min(abs(remaining), self.current_speed[axis] * dt), remaining) if remaining else 0.0
            self.position[axis] += step + self._gauss(0.0, self.noise_level)
        self.position["z"] += 0.0001 * math.sin(self.position["z"] * 10.0)
        return dict(self.position)

    def set_position(self, x: float, y: float, z: float) -> None:
        self.position.update(x=float(x), y=float(y), z=float(z))
        self.current_speed.update(x=0.0, y=0.0, z=0.0)

