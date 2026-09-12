from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from core.z_control.crtouch_contact_profile import ContactProfileConfig


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Plan the fail-closed CR Touch magnet contact profile."
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Reserved for the supervised hardware runner; currently rejected.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.execute:
        print(
            "BLOCKED: hardware execution is not enabled in this planning tool. "
            "Complete the reviewed pilot runner and explicit authorization first."
        )
        return 2

    config = ContactProfileConfig()
    points = config.points()
    print("CR TOUCH CONTACT PROFILOMETER — 3x3 PILOT PLAN")
    print(
        f"Target: height={config.target_height_mm:.1f} mm "
        f"diameter={config.target_diameter_mm:.1f} mm"
    )
    print(
        f"Z: handoff={config.fine_handoff_z_mm:.2f} "
        f"expected_trigger={config.expected_electrical_trigger_z_mm:.2f} "
        f"hard_floor={config.hard_floor_z_mm:.2f}"
    )
    print("Path:")
    for point in points:
        print(
            f"{point.index:02d}: row={point.row} col={point.column} "
            f"X{point.nozzle_x_mm:.2f} Y{point.nozzle_y_mm:.2f}"
        )
    print("Hardware execution: LOCKED pending supervised runner review.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
