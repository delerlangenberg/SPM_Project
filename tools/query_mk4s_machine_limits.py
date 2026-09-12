from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.education.config_loader import load_config
from core.motion.prusa_gcode_backend import PrusaGcodeBackend


def main() -> int:
    config = load_config()
    printer = config["printer"]
    backend = PrusaGcodeBackend(
        port=str(printer["port"]),
        baudrate=int(printer["baudrate"]),
        timeout=0.5,
        auto_detect_port=False,
    )

    commands = [
        ("Firmware", "M115"),
        ("Current position", "M114"),
        ("Endstop status", "M119"),
        ("Firmware settings", "M503"),
        ("Software endstops", "M211"),
    ]

    try:
        backend.connect()
        print("MK4S no-motion machine information query")
        print("Connected:", backend.get_state())

        for label, command in commands:
            print()
            print(f">> {label}: {command}")
            lines = backend.send_gcode(command, timeout=5.0)
            if lines:
                for line in lines:
                    print(line)
            else:
                print("(no response text)")

        print()
        print("Final state:", backend.get_state())
        return 0
    except Exception as error:
        print(f"ERROR: {error}")
        return 2
    finally:
        backend.disconnect()


if __name__ == "__main__":
    raise SystemExit(main())
