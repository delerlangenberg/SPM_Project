"""Analytic virtual sample topographies."""

from __future__ import annotations

import math
from typing import Any


SAMPLE_TYPES = ("half_ball", "square", "bravais_111", "bravais_100", "bravais_110")


class SampleGenerator:
    SAMPLE_TYPES = SAMPLE_TYPES

    def __init__(self, sample_type: str, params: dict[str, float] | None = None) -> None:
        normalized = str(sample_type).strip().lower()
        if normalized not in SAMPLE_TYPES:
            raise ValueError(f"Unsupported sample type: {sample_type}")
        self.sample_type = normalized
        self.params = dict(params or {})
        self._validate()

    def get_height_at_position(self, x: float, y: float) -> float:
        method = getattr(self, f"_{self.sample_type}")
        return max(0.0, float(method(float(x), float(y))))

    def get_topography_array(
        self,
        resolution: int,
        *,
        x_range: tuple[float, float] = (-1.0, 1.0),
        y_range: tuple[float, float] = (-1.0, 1.0),
    ) -> list[list[float]]:
        if resolution < 2:
            raise ValueError("resolution must be at least 2")
        xs = self._linspace(*x_range, resolution)
        ys = self._linspace(*y_range, resolution)
        return [[self.get_height_at_position(x, y) for x in xs] for y in ys]

    def _half_ball(self, x: float, y: float) -> float:
        radius = self._positive("radius", 0.5)
        height = self._positive("height", 0.5)
        dx = x - self.params.get("center_x", 0.0)
        dy = y - self.params.get("center_y", 0.0)
        normalized_r2 = (dx * dx + dy * dy) / (radius * radius)
        return height * math.sqrt(max(0.0, 1.0 - normalized_r2)) if normalized_r2 <= 1.0 else 0.0

    def _square(self, x: float, y: float) -> float:
        width = self._positive("width", 1.0)
        height = self._positive("height", 0.5)
        edge = max(0.0, float(self.params.get("edge_sharpness", 0.05)))
        half = width / 2.0
        dx = abs(x - self.params.get("center_x", 0.0))
        dy = abs(y - self.params.get("center_y", 0.0))
        if dx >= half or dy >= half:
            return 0.0
        if edge == 0:
            return height
        factor_x = min(1.0, max(0.0, (half - dx) / edge))
        factor_y = min(1.0, max(0.0, (half - dy) / edge))
        return height * factor_x * factor_y

    def _bravais_111(self, x: float, y: float) -> float:
        a = self._positive("lattice_constant", 0.2)
        height = self._positive("height", 0.05)
        rx, ry = self._rotated(x, y)
        a2y = a * math.sqrt(3.0) / 2.0
        n2 = round(ry / a2y)
        n1 = round((rx - n2 * a / 2.0) / a)
        dx = rx - (n1 * a + n2 * a / 2.0)
        dy = ry - n2 * a2y
        sigma = a * 0.25
        return height * math.exp(-(dx * dx + dy * dy) / (2.0 * sigma * sigma))

    def _bravais_100(self, x: float, y: float) -> float:
        a = self._positive("lattice_constant", 0.2)
        height = self._positive("height", 0.05)
        rx, ry = self._rotated(x, y)
        dx = rx - round(rx / a) * a
        dy = ry - round(ry / a) * a
        sigma = a * 0.25
        return height * math.exp(-(dx * dx + dy * dy) / (2.0 * sigma * sigma))

    def _bravais_110(self, x: float, y: float) -> float:
        a = self._positive("lattice_constant_a", 0.2)
        b = self._positive("lattice_constant_b", 0.35)
        height = self._positive("height", 0.05)
        rx, ry = self._rotated(x, y)
        dx = rx - round(rx / a) * a
        dy = ry - round(ry / b) * b
        return height * math.exp(-((dx * dx) / (2.0 * (a * 0.2) ** 2) + (dy * dy) / (2.0 * (b * 0.2) ** 2)))

    def _rotated(self, x: float, y: float) -> tuple[float, float]:
        center_x = float(self.params.get("center_x", 0.0))
        center_y = float(self.params.get("center_y", 0.0))
        angle = math.radians(float(self.params.get("rotation", 0.0)))
        dx, dy = x - center_x, y - center_y
        return dx * math.cos(angle) - dy * math.sin(angle), dx * math.sin(angle) + dy * math.cos(angle)

    def _validate(self) -> None:
        for key in ("radius", "width", "height", "lattice_constant", "lattice_constant_a", "lattice_constant_b"):
            if key in self.params and float(self.params[key]) <= 0:
                raise ValueError(f"{key} must be positive")
        if float(self.params.get("edge_sharpness", 0.0)) < 0:
            raise ValueError("edge_sharpness must be non-negative")

    def _positive(self, key: str, default: float) -> float:
        return float(self.params.get(key, default))

    @staticmethod
    def _linspace(start: float, stop: float, count: int) -> list[float]:
        return [start + (stop - start) * index / (count - 1) for index in range(count)]

