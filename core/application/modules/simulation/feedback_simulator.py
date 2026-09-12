"""Deterministic PID-style AFM/STM teaching feedback."""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass


@dataclass(frozen=True, slots=True)
class FeedbackSignals:
    deflection: float
    amplitude: float
    current: float
    z_correction: float
    error: float

    def as_dict(self) -> dict[str, float]:
        return asdict(self)


class FeedbackSimulator:
    def __init__(self, *, setpoint: float = 0.0, gain_p: float = 1.0, gain_i: float = 0.5, gain_d: float = 0.1) -> None:
        self.setpoint = float(setpoint)
        self.gain_p = float(gain_p)
        self.gain_i = float(gain_i)
        self.gain_d = float(gain_d)
        self.integral = 0.0
        self.prev_error = 0.0

    def reset(self) -> None:
        self.integral = 0.0
        self.prev_error = 0.0

    def update(self, target_height: float, current_z: float, dt: float) -> dict[str, float]:
        if dt <= 0:
            raise ValueError("dt must be positive")
        error = float(target_height) + self.setpoint - float(current_z)
        self.integral = max(-100.0, min(100.0, self.integral + error * dt))
        derivative = (error - self.prev_error) / dt
        self.prev_error = error
        correction = self.gain_p * error + self.gain_i * self.integral + self.gain_d * derivative
        signals = FeedbackSignals(
            deflection=error,
            amplitude=max(0.0, min(10.0, 1.0 + error * 0.1)),
            current=math.exp(-1.5 * abs(error)),
            z_correction=correction,
            error=error,
        )
        return signals.as_dict()

