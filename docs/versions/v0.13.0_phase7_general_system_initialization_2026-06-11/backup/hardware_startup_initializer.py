"""Read-only SPM hardware startup initializer.

Phase 7 only:
- Loads confirmed hardware profile
- Opens confirmed serial port
- Sends only read-only commands
- Returns structured initialization result

No movement.
No homing.
No scan.
"""

from dataclasses import dataclass
from datetime import datetime
import time

import serial

from core.system.hardware_initialized_profile import get_motion_controller_settings


READONLY_STARTUP_COMMANDS = ("M115", "M105", "M119")


@dataclass
class StartupCommandResult:
    command: str
    success: bool
    response_lines: list[str]


@dataclass
class HardwareStartupResult:
    success: bool
    port: str
    baudrate: int
    timestamp: str
    command_results: list[StartupCommandResult]


def run_readonly_hardware_startup(
    port: str | None = None,
    baudrate: int | None = None,
    timeout: float = 2.0,
    settle_seconds: float = 2.0,
) -> HardwareStartupResult:
    settings = get_motion_controller_settings()
    selected_port = port or settings["port"]
    selected_baudrate = baudrate or int(settings["baudrate"])

    command_results: list[StartupCommandResult] = []

    with serial.Serial(selected_port, selected_baudrate, timeout=timeout) as ser:
        time.sleep(settle_seconds)

        for command in READONLY_STARTUP_COMMANDS:
            ser.write((command + "\n").encode("ascii"))
            time.sleep(1.0)

            response_lines: list[str] = []
            end_time = time.time() + 3.0

            while time.time() < end_time:
                line = ser.readline().decode(errors="replace").strip()
                if line:
                    response_lines.append(line)
                if line == "ok":
                    break

            command_results.append(
                StartupCommandResult(
                    command=command,
                    success=any("ok" in line.lower() for line in response_lines),
                    response_lines=response_lines,
                )
            )

    return HardwareStartupResult(
        success=all(result.success for result in command_results),
        port=selected_port,
        baudrate=selected_baudrate,
        timestamp=datetime.now().isoformat(timespec="seconds"),
        command_results=command_results,
    )
