"""CLI entry point for safe SPM hardware commands.

Phase 6 only:
- POWER_ON
- POWER_OFF
- INFO
- SAFE_STOP

No motion commands.
No scan commands.
"""

import argparse

from core.hardware.hardware_command_bus import SimulatedHardwareCommandBus
from core.hardware.hardware_command_log import append_hardware_command_log


def main() -> int:
    parser = argparse.ArgumentParser(description="Safe SPM hardware command CLI")
    parser.add_argument(
        "command",
        choices=["POWER_ON", "POWER_OFF", "INFO", "SAFE_STOP"],
        help="Safe hardware command to execute",
    )
    args = parser.parse_args()

    bus = SimulatedHardwareCommandBus()
    result = bus.send(args.command)
    log_path = append_hardware_command_log(result)

    print(f"timestamp={result.timestamp}")
    print(f"command={result.command}")
    print(f"success={result.success}")
    print(f"response={result.response}")
    print(f"log={log_path}")

    return 0 if result.success else 1


if __name__ == "__main__":
    raise SystemExit(main())
