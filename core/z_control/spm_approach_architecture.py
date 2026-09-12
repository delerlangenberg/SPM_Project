"""Fail-closed two-stage SPM approach model.

The CR Touch is a coarse contact/safety probe. It is not accepted as the
continuous fine-profile sensor because physical contact precedes its electrical
trigger by substantial pin travel.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ApproachPhase(str, Enum):
    SAFE_RETRACTED = "safe_retracted"
    COARSE_CLEAR = "coarse_clear"
    FINE_HANDOFF = "fine_handoff"
    PIN_COMPRESSION = "pin_compression"
    CRTOUCH_TRIGGERED = "crtouch_triggered"
    HARD_FLOOR = "hard_floor"


@dataclass(frozen=True)
class CRTouchCoarseCalibration:
    target_surface_z_mm: float
    first_physical_contact_z_mm: float
    electrical_trigger_z_mm: float
    hard_floor_z_mm: float
    safe_retract_z_mm: float = 120.0
    fine_handoff_clearance_mm: float = 1.0

    def validate(self) -> None:
        if not (
            self.safe_retract_z_mm
            > self.fine_handoff_z_mm
            > self.first_physical_contact_z_mm
            > self.electrical_trigger_z_mm
            > self.hard_floor_z_mm
            > self.target_surface_z_mm
        ):
            raise ValueError("Invalid CR Touch coarse-approach Z ordering.")
        if self.pin_overtravel_mm <= 0:
            raise ValueError("CR Touch pin overtravel must be positive.")

    @property
    def pin_overtravel_mm(self) -> float:
        return self.first_physical_contact_z_mm - self.electrical_trigger_z_mm

    @property
    def fine_handoff_z_mm(self) -> float:
        return self.first_physical_contact_z_mm + self.fine_handoff_clearance_mm

    def estimated_surface_gap_mm(self, z_mm: float) -> float:
        return max(0.0, z_mm - self.first_physical_contact_z_mm)

    def estimated_pin_compression_mm(self, z_mm: float) -> float:
        return max(
            0.0,
            min(self.pin_overtravel_mm, self.first_physical_contact_z_mm - z_mm),
        )

    def phase_at(self, z_mm: float) -> ApproachPhase:
        if z_mm >= self.safe_retract_z_mm:
            return ApproachPhase.SAFE_RETRACTED
        if z_mm > self.fine_handoff_z_mm:
            return ApproachPhase.COARSE_CLEAR
        if z_mm > self.first_physical_contact_z_mm:
            return ApproachPhase.FINE_HANDOFF
        if z_mm > self.electrical_trigger_z_mm:
            return ApproachPhase.PIN_COMPRESSION
        if z_mm > self.hard_floor_z_mm:
            return ApproachPhase.CRTOUCH_TRIGGERED
        return ApproachPhase.HARD_FLOOR


@dataclass(frozen=True)
class FineProfilingReadiness:
    sensor_name: str = "UNSELECTED"
    actuator_name: str = "UNSELECTED"
    sensor_connected: bool = False
    sensor_calibrated: bool = False
    continuous_feedback_verified: bool = False
    actuator_connected: bool = False
    actuator_calibrated: bool = False
    closed_loop_verified: bool = False
    coarse_repeatability_cycles: int = 0
    coarse_repeatability_stddev_mm: float | None = None

    def blockers(self) -> tuple[str, ...]:
        blockers: list[str] = []
        if self.coarse_repeatability_cycles < 10:
            blockers.append("At least 10 CR Touch coarse repeatability cycles are required.")
        if self.coarse_repeatability_stddev_mm is None:
            blockers.append("CR Touch coarse repeatability standard deviation is missing.")
        if self.sensor_name in {"", "UNSELECTED"}:
            blockers.append("Fine profiling sensor is not selected.")
        if not self.sensor_connected:
            blockers.append("Fine profiling sensor is not connected.")
        if not self.sensor_calibrated:
            blockers.append("Fine profiling sensor is not calibrated.")
        if not self.continuous_feedback_verified:
            blockers.append("Continuous fine-sensor feedback is not verified.")
        if self.actuator_name in {"", "UNSELECTED"}:
            blockers.append("Fine Z actuator is not selected.")
        if not self.actuator_connected:
            blockers.append("Fine Z actuator is not connected.")
        if not self.actuator_calibrated:
            blockers.append("Fine Z actuator is not calibrated.")
        if not self.closed_loop_verified:
            blockers.append("Fine-sensor/fine-actuator closed loop is not verified.")
        return tuple(blockers)

    @property
    def profiling_allowed(self) -> bool:
        return not self.blockers()


def two_stage_plan(calibration: CRTouchCoarseCalibration) -> tuple[str, ...]:
    calibration.validate()
    return (
        f"Retract with xBuddy to Z{calibration.safe_retract_z_mm:.3f}.",
        "Move XY only while safely retracted.",
        "Reset, stow and deploy CR Touch; require a LOW baseline.",
        (
            f"Coarse-descend only to Z{calibration.fine_handoff_z_mm:.3f}; "
            "normal profiling must hand off before physical CR Touch contact."
        ),
        "Require a healthy, calibrated continuous fine-sensor reading.",
        "Use only the commissioned fine-Z actuator for the profiling approach.",
        (
            f"Treat CR Touch contact near Z{calibration.first_physical_contact_z_mm:.3f} "
            "as an abnormal safety event, not a measurement point."
        ),
        (
            f"On CR Touch electrical trigger near Z{calibration.electrical_trigger_z_mm:.3f}, "
            f"immediately retract to Z{calibration.safe_retract_z_mm:.3f}."
        ),
        (
            f"Never continue below hard floor Z{calibration.hard_floor_z_mm:.3f}; "
            "transport loss also causes retract."
        ),
    )
