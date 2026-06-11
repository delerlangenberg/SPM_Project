"""Safe hardware command layer for SPM Phase 6.1.

This module does NOT move motors.
It only defines power/status/info command exchange.
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class HardwareCommandResult:
    command: str
    success: bool
    response: str
    timestamp: str


class SimulatedHardwareCommandBus:
    """Safe simulated command bus before connecting real hardware."""

    def __init__(self) -> None:
        self.powered_on = False
        self.history: list[HardwareCommandResult] = []

    def send(self, command: str) -> HardwareCommandResult:
        command_clean = command.strip().upper()

        if command_clean == "POWER_ON":
            self.powered_on = True
            response = "OK: POWER ON"
            success = True

        elif command_clean == "POWER_OFF":
            self.powered_on = False
            response = "OK: POWER OFF"
            success = True

        elif command_clean == "INFO":
            state = "ON" if self.powered_on else "OFF"
            response = f"OK: SPM HARDWARE SIMULATED; POWER={state}"
            success = True

        elif command_clean == "SAFE_STOP":
            self.powered_on = False
            response = "OK: SAFE STOP; POWER OFF"
            success = True

        else:
            response = f"ERROR: UNKNOWN COMMAND {command_clean}"
            success = False

        result = HardwareCommandResult(
            command=command_clean,
            success=success,
            response=response,
            timestamp=datetime.now().isoformat(timespec="seconds"),
        )
        self.history.append(result)
        return result
