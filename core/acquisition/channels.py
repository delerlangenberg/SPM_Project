from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from core.education.synthetic_signal import synthetic_surface_signal


@dataclass(frozen=True)
class SensorSample:
    timestamp: str
    x: float
    y: float
    z: float
    channel: str
    value: float
    unit: str


class AcquisitionChannel(Protocol):
    name: str
    unit: str

    def read_sample(self, *, x: float, y: float, z: float) -> SensorSample:
        """Read one synchronized sensor sample at the current scan position."""


class SimulatedSurfaceChannel:
    name = "simulated_surface"
    unit = "a.u."

    def read_sample(self, *, x: float, y: float, z: float) -> SensorSample:
        return SensorSample(
            timestamp=datetime.now().isoformat(timespec="seconds"),
            x=float(x),
            y=float(y),
            z=float(z),
            channel=self.name,
            value=float(synthetic_surface_signal(x, y)),
            unit=self.unit,
        )


def available_default_channels() -> list[AcquisitionChannel]:
    return [SimulatedSurfaceChannel()]
