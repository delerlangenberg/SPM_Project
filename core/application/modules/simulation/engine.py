"""Orchestrates the virtual sample, feedback loop, and XYZ scanner."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import math
from typing import Any

from .feedback_simulator import FeedbackSimulator
from .sample_generator import SampleGenerator
from .scanner_controller import ScannerController


class SimulationState(str, Enum):
    DISABLED = "DISABLED"
    IDLE = "IDLE"
    APPROACHING = "APPROACHING"
    SCANNING = "SCANNING"
    RETRACTING = "RETRACTING"


@dataclass(slots=True)
class _NullLogger:
    def log(self, _message: str, *_args: Any, **_kwargs: Any) -> None:
        return None


class SimulationEngine:
    def __init__(self, logger: Any | None = None, *, scanner: ScannerController | None = None) -> None:
        self.logger = logger or _NullLogger()
        self.is_active = False
        self.current_sample: SampleGenerator | None = None
        self.scanner = scanner or ScannerController()
        self.feedback = FeedbackSimulator()
        self.scan_state = SimulationState.DISABLED
        self.sample_config: dict[str, float] = {}
        self.scan_params: dict[str, Any] = {}
        self.last_feedback: dict[str, float] = {}

    @property
    def scanner_position(self) -> tuple[float, float, float]:
        p = self.scanner.position
        return p["x"], p["y"], p["z"]

    def enable(self, sample_type: str, params: dict[str, float] | None = None) -> bool:
        self.current_sample = SampleGenerator(sample_type, params)
        self.sample_config = dict(params or {})
        self.feedback.reset()
        self.is_active = True
        self.scan_state = SimulationState.IDLE
        self.logger.log(f"[SIMULATION] Enabled sample {sample_type}", "event", source="simulation")
        return True

    def disable(self) -> bool:
        self.stop_scan()
        self.is_active = False
        self.current_sample = None
        self.scan_state = SimulationState.DISABLED
        self.logger.log("[SIMULATION] Disabled; hardware routing restored", "event", source="simulation")
        return True

    def move_to_position(self, x: float, y: float, z: float, *, dt: float = 0.05) -> dict[str, float]:
        self._require_active()
        actual = self.scanner.move_to(x, y, z, dt)
        height = self.current_sample.get_height_at_position(actual["x"], actual["y"])
        signals = self.feedback.update(height, actual["z"], dt)
        self.last_feedback = signals
        return {**actual, "surface_height": height, **signals}

    def start_scan(self, scan_params: dict[str, Any]) -> bool:
        self._require_active()
        required = {"x_min", "x_max", "y_min", "y_max", "x_points", "y_points"}
        missing = required.difference(scan_params)
        if missing:
            raise ValueError(f"Missing scan parameters: {', '.join(sorted(missing))}")
        self.scan_params = dict(scan_params)
        self.scan_state = SimulationState.SCANNING
        self.logger.log("[SIMULATION] Virtual raster started", "event", source="simulation")
        return True

    def stop_scan(self) -> bool:
        if self.is_active and self.scan_state is SimulationState.SCANNING:
            self.logger.log("[SIMULATION] Virtual raster stopped", "event", source="simulation")
        self.scan_state = SimulationState.IDLE if self.is_active else SimulationState.DISABLED
        return True

    def scan_point(self, x: float, y: float, *, z_setpoint: float = 0.0, dt: float = 0.01) -> dict[str, float]:
        self._require_active()
        height = self.current_sample.get_height_at_position(x, y)
        target_z = z_setpoint + height
        self.scanner.set_position(x, y, target_z)
        tracking_error = 0.002 * math.sin(x * 1.7 + y * 2.3)
        signals = self.feedback.update(height, height - tracking_error, dt)
        self.last_feedback = signals
        return {"x": x, "y": y, "z": target_z, "surface_height": height, **signals}

    def get_current_feedback(self) -> dict[str, float]:
        return dict(self.last_feedback)

    def get_topography_array(self, resolution: int, **ranges: Any) -> list[list[float]]:
        self._require_active()
        return self.current_sample.get_topography_array(resolution, **ranges)

    def _require_active(self) -> None:
        if not self.is_active or self.current_sample is None:
            raise RuntimeError("Simulation is not enabled")
