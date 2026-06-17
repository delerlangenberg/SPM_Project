"""Focused MK4S Z auto-approach sequence for the Educational SPM project."""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path

import serial

from core.system.hardware_initialized_profile import get_motion_controller_settings, load_hardware_initialized_profile


@dataclass(frozen=True)
class ZAutoApproachResult:
    success: bool
    dry_run: bool
    commands: list[str]
    responses: list[str]
    final_z: float
    message: str


def confirmed_approach_reference() -> dict:
    profile = load_hardware_initialized_profile()
    return profile["hardware_initialized_profile"]["z_approach_reference"]


def planned_auto_approach_commands(*, retract_after: bool = False) -> list[str]:
    reference = confirmed_approach_reference()
    auto = reference["auto_step_approach_confirmed"]
    x = float(auto["x"])
    y = float(auto["y"])
    start_z = float(auto["start_z"])
    stop_z = float(auto["stop_z"])
    feedrate = float(auto["feedrate"])
    steps = [float(value) for value in auto["step_sequence"]]
    safe_retract_z = float(auto["safe_retract_z"])

    commands = [
        "M114",
        "M17",
        "G90",
        f"G1 Z{start_z:.2f} F600",
        "M400",
        f"G1 X{x:.2f} Y{y:.2f} F1200",
        "M400",
        "M114",
    ]
    for z_value in steps:
        if z_value < stop_z:
            raise ValueError(f"planned Z step {z_value} is below confirmed stop Z {stop_z}")
        commands.extend([f"G1 Z{z_value:.2f} F{feedrate:.0f}", "M400", "M114"])
    if retract_after:
        commands.extend([f"G1 Z{safe_retract_z:.2f} F600", "M400", "M114"])
    return commands


def _read_until_ok(ser: serial.Serial, *, timeout_s: float) -> list[str]:
    lines: list[str] = []
    end = time.time() + timeout_s
    while time.time() < end:
        line = ser.readline().decode(errors="replace").strip()
        if not line:
            continue
        lines.append(line)
        if line.lower().startswith("echo:busy"):
            end = time.time() + timeout_s
            continue
        if line.lower() == "ok" or line.lower().startswith("ok "):
            return lines
    raise TimeoutError("No ok received during Z auto approach")


def run_mk4s_z_auto_approach(
    *,
    execute: bool = False,
    retract_after: bool = False,
    raw_log_path: str | Path = "logs/mk4s_z_auto_approach_raw.txt",
) -> ZAutoApproachResult:
    commands = planned_auto_approach_commands(retract_after=retract_after)
    reference = confirmed_approach_reference()
    auto = reference["auto_step_approach_confirmed"]
    final_z = float(auto["safe_retract_z"] if retract_after else auto["stop_z"])
    if not execute:
        return ZAutoApproachResult(
            success=True,
            dry_run=True,
            commands=commands,
            responses=[],
            final_z=final_z,
            message="Preview only. No MK4S movement was sent.",
        )

    settings = get_motion_controller_settings()
    raw_path = Path(raw_log_path)
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    responses: list[str] = []
    with serial.Serial(settings["port"], int(settings["baudrate"]), timeout=2) as ser:
        time.sleep(2)
        with raw_path.open("a", encoding="utf-8") as log:
            log.write(f"\n=== MK4S Z AUTO APPROACH {time.strftime('%Y-%m-%d %H:%M:%S')} ===\n")
            for command in commands:
                log.write(f">>> {command}\n")
                ser.write((command + "\n").encode("ascii", errors="replace"))
                ser.flush()
                timeout = 90.0 if command.startswith("G1 ") or command == "M400" else 8.0
                lines = _read_until_ok(ser, timeout_s=timeout)
                responses.extend(f"{command}: {line}" for line in lines)
                for line in lines:
                    log.write(f"{line}\n")

    return ZAutoApproachResult(
        success=True,
        dry_run=False,
        commands=commands,
        responses=responses,
        final_z=final_z,
        message=f"MK4S Z auto approach completed. Final Z={final_z:.2f}. Raw log: {raw_path}",
    )
