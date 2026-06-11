"""Persistent log support for safe SPM hardware commands."""

from pathlib import Path
from core.hardware.hardware_command_bus import HardwareCommandResult


def append_hardware_command_log(
    result: HardwareCommandResult,
    log_path: str | Path = "logs/hardware_command_log.csv",
) -> Path:
    path = Path(log_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    new_file = not path.exists()

    with path.open("a", encoding="utf-8", newline="") as file:
        if new_file:
            file.write("timestamp,command,success,response\n")

        safe_response = result.response.replace('"', '""')
        file.write(
            f'{result.timestamp},{result.command},{result.success},"{safe_response}"\n'
        )

    return path
