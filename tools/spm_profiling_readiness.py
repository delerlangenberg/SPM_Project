from __future__ import annotations

import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from core.z_control.spm_approach_architecture import (
    CRTouchCoarseCalibration,
    FineProfilingReadiness,
    two_stage_plan,
)


CONFIG_PATH = PROJECT_ROOT / "config" / "spm_two_stage_approach.json"


def main() -> int:
    data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    reference = data["reference"]
    fine = data["fine_profiling"]
    calibration = CRTouchCoarseCalibration(
        target_surface_z_mm=reference["target_height_mm"],
        first_physical_contact_z_mm=reference[
            "first_physical_contact_z_mm_approx"
        ],
        electrical_trigger_z_mm=reference["electrical_trigger_z_mm"],
        hard_floor_z_mm=reference["hard_floor_z_mm"],
        safe_retract_z_mm=reference["safe_retract_z_mm"],
        fine_handoff_clearance_mm=reference["fine_handoff_clearance_mm"],
    )
    calibration.validate()

    readiness = FineProfilingReadiness(
        sensor_name=fine["sensor_name"],
        actuator_name=fine["actuator_name"],
        sensor_connected=fine["sensor_connected"],
        sensor_calibrated=fine["sensor_calibrated"],
        continuous_feedback_verified=fine["continuous_feedback_verified"],
        actuator_connected=fine["actuator_connected"],
        actuator_calibrated=fine["actuator_calibrated"],
        closed_loop_verified=fine["closed_loop_verified"],
        coarse_repeatability_cycles=fine.get("coarse_repeatability_cycles", 0),
        coarse_repeatability_stddev_mm=fine.get(
            "coarse_repeatability_stddev_mm"
        ),
    )

    print("SPM TWO-STAGE APPROACH READINESS")
    print(f"Coarse CR Touch: VALIDATED; overtravel={calibration.pin_overtravel_mm:.2f} mm")
    print(f"Fine handoff: Z{calibration.fine_handoff_z_mm:.2f}")
    print(f"Fine profiling: {'READY' if readiness.profiling_allowed else 'LOCKED'}")
    for blocker in readiness.blockers():
        print(f"- {blocker}")
    print("Plan:")
    for number, step in enumerate(two_stage_plan(calibration), start=1):
        print(f"{number}. {step}")
    return 0 if readiness.profiling_allowed else 2


if __name__ == "__main__":
    raise SystemExit(main())
