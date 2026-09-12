from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = PROJECT_ROOT / "config" / "mounted_crtouch_commissioning.json"
sys.path.insert(0, str(PROJECT_ROOT))

from core.z_control.mounted_crtouch_commissioning import MountedProbeCommissioning


def main() -> int:
    data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    target = data["target"]
    probe = data["mounted_probe"]
    motion = data["motion"]
    evidence = data["required_evidence"]

    setup = MountedProbeCommissioning(
        target_center_x_mm=target["center_x_mm"],
        target_center_y_mm=target["center_y_mm"],
        target_height_mm=target["height_mm"],
        probe_offset_x_mm=probe["offset_x_mm"],
        probe_offset_y_mm=probe["offset_y_mm"],
        trigger_clearance_above_surface_mm=probe[
            "trigger_clearance_above_surface_mm"
        ],
        hard_floor_z_mm=motion["hard_floor_z_mm"],
        safe_retract_z_mm=motion["safe_retract_z_mm"],
        fine_step_mm=motion["fine_step_mm"],
        approach_speed_mm_s=motion["approach_speed_mm_s"],
        **evidence,
    )

    blockers = setup.blockers()
    print("SPM MOUNTED CR TOUCH READINESS")
    print(f"Config: {CONFIG_PATH}")
    print(f"Status: {'BLOCKED' if blockers else 'READY FOR SUPERVISED FIRST TOUCH'}")
    if blockers:
        for number, blocker in enumerate(blockers, start=1):
            print(f"{number}. {blocker}")
        return 2

    print(f"Nozzle target: X{setup.nozzle_target_x_mm:.3f} Y{setup.nozzle_target_y_mm:.3f}")
    print(f"Expected trigger Z: {setup.expected_trigger_z_mm:.3f}")
    for number, instruction in enumerate(setup.motion_plan(), start=1):
        print(f"{number}. {instruction}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
