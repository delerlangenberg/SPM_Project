from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class MountedProbeCommissioning:
    target_center_x_mm: Optional[float]
    target_center_y_mm: Optional[float]
    target_height_mm: float
    probe_offset_x_mm: Optional[float]
    probe_offset_y_mm: Optional[float]
    trigger_clearance_above_surface_mm: Optional[float]
    hard_floor_z_mm: Optional[float]
    safe_retract_z_mm: float = 120.0
    fine_step_mm: float = 0.1
    approach_speed_mm_s: float = 0.1
    bed_z_reference_verified: bool = False
    target_secured: bool = False
    probe_mount_rigid: bool = False
    probe_vertical: bool = False
    mk4s_m114_verified: bool = False
    mega_identity_verified: bool = False
    bench_repeatability_5_of_5: bool = False
    operator_watching: bool = False

    def blockers(self) -> list[str]:
        blockers: list[str] = []

        required_values = (
            ("Target center X", self.target_center_x_mm),
            ("Target center Y", self.target_center_y_mm),
            ("Mounted probe X offset", self.probe_offset_x_mm),
            ("Mounted probe Y offset", self.probe_offset_y_mm),
            (
                "Probe trigger clearance above the surface",
                self.trigger_clearance_above_surface_mm,
            ),
            ("Hard Z floor", self.hard_floor_z_mm),
        )
        for label, value in required_values:
            if value is None:
                blockers.append(f"{label} is not recorded.")

        required_evidence = (
            ("Bed Z reference is not verified.", self.bed_z_reference_verified),
            ("Target is not confirmed secured.", self.target_secured),
            ("Probe mount rigidity is not confirmed.", self.probe_mount_rigid),
            ("Probe vertical orientation is not confirmed.", self.probe_vertical),
            ("Live MK4S M114 position is not verified.", self.mk4s_m114_verified),
            ("Mega identity is not verified.", self.mega_identity_verified),
            (
                "CR Touch 5-of-5 bench repeatability is not verified.",
                self.bench_repeatability_5_of_5,
            ),
            ("Operator-watch confirmation is missing.", self.operator_watching),
        )
        blockers.extend(message for message, passed in required_evidence if not passed)

        if self.fine_step_mm <= 0 or self.fine_step_mm > 0.1:
            blockers.append("Fine step must be greater than 0 and no more than 0.1 mm.")
        if self.approach_speed_mm_s <= 0 or self.approach_speed_mm_s > 0.1:
            blockers.append(
                "First mounted approach speed must be greater than 0 and no more than 0.1 mm/s."
            )
        if self.safe_retract_z_mm < 120.0:
            blockers.append("Safe retract must remain at or above Z120 for first mounted tests.")

        if (
            self.hard_floor_z_mm is not None
            and self.trigger_clearance_above_surface_mm is not None
        ):
            expected_trigger = (
                self.target_height_mm + self.trigger_clearance_above_surface_mm
            )
            if self.hard_floor_z_mm >= expected_trigger:
                blockers.append(
                    "Hard Z floor must be below the expected trigger Z so the search window can cross it."
                )
            if expected_trigger - self.hard_floor_z_mm > 1.0:
                blockers.append(
                    "Hard Z floor is more than 1.0 mm below expected trigger Z."
                )

        return blockers

    @property
    def nozzle_target_x_mm(self) -> Optional[float]:
        if self.target_center_x_mm is None or self.probe_offset_x_mm is None:
            return None
        return self.target_center_x_mm - self.probe_offset_x_mm

    @property
    def nozzle_target_y_mm(self) -> Optional[float]:
        if self.target_center_y_mm is None or self.probe_offset_y_mm is None:
            return None
        return self.target_center_y_mm - self.probe_offset_y_mm

    @property
    def expected_trigger_z_mm(self) -> Optional[float]:
        if self.trigger_clearance_above_surface_mm is None:
            return None
        return self.target_height_mm + self.trigger_clearance_above_surface_mm

    def motion_plan(self) -> list[str]:
        blockers = self.blockers()
        if blockers:
            raise RuntimeError("Mounted CR Touch motion is blocked: " + " ".join(blockers))

        assert self.nozzle_target_x_mm is not None
        assert self.nozzle_target_y_mm is not None
        assert self.hard_floor_z_mm is not None

        return [
            "Read and verify MK4S M114; do not home automatically.",
            f"Retract Z to {self.safe_retract_z_mm:.3f} mm.",
            (
                f"Move nozzle to X{self.nozzle_target_x_mm:.3f} "
                f"Y{self.nozzle_target_y_mm:.3f} so the mounted probe is over the target center."
            ),
            "Reset, stow, then deploy CR Touch; require LOW trigger baseline.",
            (
                f"Descend only in steps no larger than {self.fine_step_mm:.3f} mm "
                f"at {self.approach_speed_mm_s:.3f} mm/s."
            ),
            "After every completed Z step, read the Mega trigger state.",
            (
                f"On first rising trigger, latch contact Z and retract to "
                f"{self.safe_retract_z_mm:.3f} mm."
            ),
            (
                f"If no trigger by Z{self.hard_floor_z_mm:.3f}, abort and retract; "
                "never continue downward."
            ),
        ]
