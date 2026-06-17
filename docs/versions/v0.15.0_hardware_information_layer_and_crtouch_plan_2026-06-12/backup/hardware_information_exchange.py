"""Read-only hardware information exchange for the hardware-test layer.

This module is the backend for future GUI hardware-test buttons. It only
allows information/status commands and rejects motion by construction.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable

import serial

from core.system.hardware_initialized_profile import get_motion_controller_settings


READONLY_HARDWARE_ACTIONS: dict[str, str] = {
    "IDENTITY": "M115",
    "TEMPERATURE": "M105",
    "ENDSTOPS": "M119",
    "POSITION": "M114",
}
FORBIDDEN_GCODE_PREFIXES = ("G0", "G1", "G28", "G29", "M17", "M18", "M84", "M112")


@dataclass(frozen=True)
class HardwareInformationResult:
    action: str
    command: str
    success: bool
    response_lines: list[str]
    timestamp: str


def assert_readonly_command(command: str) -> None:
    command_clean = command.strip().upper()
    for prefix in FORBIDDEN_GCODE_PREFIXES:
        if command_clean == prefix or command_clean.startswith(prefix + " "):
            raise ValueError(f"Forbidden motion/safety command in read-only layer: {command_clean}")


def action_commands(action: str) -> list[tuple[str, str]]:
    action_clean = action.strip().upper()
    if action_clean == "ALL":
        return list(READONLY_HARDWARE_ACTIONS.items())
    if action_clean not in READONLY_HARDWARE_ACTIONS:
        allowed = ", ".join(["ALL", *READONLY_HARDWARE_ACTIONS.keys()])
        raise ValueError(f"Unknown hardware information action {action!r}. Allowed: {allowed}")
    return [(action_clean, READONLY_HARDWARE_ACTIONS[action_clean])]


def run_with_transport(
    action: str,
    send_command: Callable[[str], list[str]],
) -> list[HardwareInformationResult]:
    results: list[HardwareInformationResult] = []
    for action_name, command in action_commands(action):
        assert_readonly_command(command)
        lines = send_command(command)
        success = any(line.strip().lower() == "ok" or line.strip().lower().startswith("ok ") for line in lines)
        results.append(
            HardwareInformationResult(
                action=action_name,
                command=command,
                success=success,
                response_lines=lines,
                timestamp=datetime.now().isoformat(timespec="seconds"),
            )
        )
    return results


def run_real_information_exchange(
    action: str,
    *,
    port: str | None = None,
    baudrate: int | None = None,
    timeout: float = 2.0,
    response_window_s: float = 5.0,
) -> list[HardwareInformationResult]:
    settings = get_motion_controller_settings()
    selected_port = port or settings["port"]
    selected_baudrate = int(baudrate or settings["baudrate"])

    def send(command: str) -> list[str]:
        import time

        lines: list[str] = []
        with serial.Serial(selected_port, selected_baudrate, timeout=timeout) as ser:
            time.sleep(2.0)
            ser.write((command + "\n").encode("ascii", errors="replace"))
            end = time.time() + response_window_s
            while time.time() < end:
                line = ser.readline().decode(errors="replace").strip()
                if line:
                    lines.append(line)
                if line == "ok" or line.startswith("ok "):
                    break
        return lines

    return run_with_transport(action, send)


def append_information_exchange_log(
    results: list[HardwareInformationResult],
    log_path: str | Path = "logs/hardware_information_exchange_log.csv",
) -> Path:
    path = Path(log_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    new_file = not path.exists()
    with path.open("a", encoding="utf-8", newline="") as handle:
        if new_file:
            handle.write("timestamp,action,command,success,response\n")
        for result in results:
            response = " | ".join(result.response_lines).replace('"', '""')
            handle.write(
                f'{result.timestamp},{result.action},{result.command},{result.success},"{response}"\n'
            )
    return path
