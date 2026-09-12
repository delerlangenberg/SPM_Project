from __future__ import annotations

import sys
import time
from pathlib import Path

import serial

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from tools.run_crtouch_magnet_profile import (
    mega_command,
    move_z,
    printer_command,
    printer_position,
    wait_for_motion,
)


def main() -> int:
    with serial.Serial("COM6", 115200, timeout=0.4) as printer, serial.Serial(
        "COM8", 115200, timeout=0.4
    ) as mega:
        time.sleep(2.5)
        printer.reset_input_buffer()
        mega.reset_input_buffer()
        _, _, z = printer_position(printer)
        printer_command(printer, "G90", 5)
        alignment_z = 19.7
        if z < alignment_z:
            move_z(printer, 25.0, 300)
        printer_command(printer, "G1 X125.000 Y105.000 F1200", 10)
        wait_for_motion(printer, 30)
        move_z(printer, alignment_z, 60)
        mega_command(mega, "RESET")
        mega_command(mega, "STOW")
        mega_command(mega, "DEPLOY")
        mega_command(mega, "CLEAR_TRIGGER")
        mega_command(mega, "APPROACH 19.70 1.00")
        print(f"ALIGNMENT_READY position={printer_position(printer)} pin=DEPLOYED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
