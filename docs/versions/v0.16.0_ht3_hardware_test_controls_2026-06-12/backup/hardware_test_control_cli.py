"""CLI for supervised MK4S hardware test controls.

Default mode is dry-run planning. Real movement requires --execute.
"""

from __future__ import annotations

import argparse

from core.system.hardware_test_controls import (
    DEFAULT_STEP_MM,
    HARDWARE_TEST_ACTIONS,
    append_hardware_test_log,
    run_hardware_test_action,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Educational SPM supervised hardware test controls")
    parser.add_argument("action", choices=HARDWARE_TEST_ACTIONS)
    parser.add_argument("--step-mm", type=float, default=DEFAULT_STEP_MM)
    parser.add_argument("--execute", action="store_true", help="Actually send commands to hardware.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = run_hardware_test_action(args.action, step_mm=args.step_mm, execute=args.execute)
    log_path = append_hardware_test_log(result)

    print(f"timestamp={result.timestamp}")
    print(f"action={result.action}")
    print(f"success={result.success}")
    print(f"commands={' | '.join(result.commands)}")
    print(f"before_position={result.before_position}")
    print(f"after_position={result.after_position}")
    print(f"response={result.response}")
    print(f"log={log_path}")
    if not args.execute:
        print("DRY RUN ONLY. Use --execute only with supervised clear hardware path.")

    return 0 if result.success else 1


if __name__ == "__main__":
    raise SystemExit(main())
