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


@dataclass(frozen=True)
class ZManualMoveResult:
    success: bool
    command: str
    responses: list[str]
    target_z: float
    message: str


def confirmed_approach_reference() -> dict:
    profile = load_hardware_initialized_profile()
    return profile["hardware_initialized_profile"]["z_approach_reference"]


def planned_auto_approach_commands(
    *,
    setpoint_distance_mm: float = 0.0,
    retract_after: bool = False,
) -> list[str]:
    reference = confirmed_approach_reference()
    auto = reference["auto_step_approach_confirmed"]
    x = float(auto["x"])
    y = float(auto["y"])
    start_z = float(auto["start_z"])
    contact_z = float(reference["manual_near_contact_z"])
    minimum_z = float(reference["do_not_go_below_without_contact_detection"])
    stop_z = contact_z + float(setpoint_distance_mm)
    if stop_z < minimum_z:
        raise ValueError(f"Approach target Z {stop_z:.2f} is below safe minimum Z {minimum_z:.2f}")
    if stop_z > start_z:
        raise ValueError(f"Approach target Z {stop_z:.2f} is above start Z {start_z:.2f}")
    feedrate = float(auto["feedrate"])
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
    # Build a descending Z approach path that never goes below the requested stop_z.
    #
    # Previous behavior always included 60.0 mm:
    #     [110, 100, 90, 80, 70, 60]
    # This was unsafe/confusing when the requested setpoint produced a stop_z
    # above 60 mm, because the planner still tried to descend to 60 mm.
    #
    # New behavior:
    # - start from coarse waypoints below start_z
    # - keep only waypoints that are still above or equal to stop_z
    # - then add 1 mm fine steps until stop_z
    # - finally add stop_z exactly
    coarse_waypoints = [110.0, 100.0, 90.0, 80.0, 70.0, 60.0]
    steps = [z for z in coarse_waypoints if start_z > z >= stop_z]

    current = steps[-1] if steps else start_z
    while current - 1.0 > stop_z:
        current -= 1.0
        steps.append(current)

    if not steps or steps[-1] != stop_z:
        steps.append(stop_z)

    for z_value in steps:
        if z_value < stop_z:
            raise ValueError(f"planned Z step {z_value} is below requested stop Z {stop_z}")
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
    setpoint_distance_mm: float = 0.0,
    retract_after: bool = False,
    raw_log_path: str | Path = "logs/mk4s_z_auto_approach_raw.txt",
) -> ZAutoApproachResult:
    commands = planned_auto_approach_commands(setpoint_distance_mm=setpoint_distance_mm, retract_after=retract_after)
    reference = confirmed_approach_reference()
    auto = reference["auto_step_approach_confirmed"]
    final_z = float(auto["safe_retract_z"] if retract_after else reference["manual_near_contact_z"] + setpoint_distance_mm)
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


def _parse_z_from_lines(lines: list[str]) -> float | None:
    import re

    joined = " ".join(lines)
    match = re.search(r"\bZ:\s*(-?\d+(?:\.\d+)?)", joined)
    return float(match.group(1)) if match else None


def run_mk4s_z_manual_step(
    *,
    direction: str,
    step_mm: float,
    execute: bool = False,
) -> ZManualMoveResult:
    if step_mm <= 0:
        raise ValueError("step_mm must be positive")
    direction_clean = direction.strip().lower()
    if direction_clean not in {"up", "down"}:
        raise ValueError("direction must be 'up' or 'down'")

    if not execute:
        sign = 1.0 if direction_clean == "up" else -1.0
        return ZManualMoveResult(
            success=True,
            command=f"preview current Z {'+' if sign > 0 else '-'} {step_mm:.2f}",
            responses=[],
            target_z=0.0,
            message="Preview only. No MK4S movement was sent.",
        )

    settings = get_motion_controller_settings()
    reference = confirmed_approach_reference()
    safe_min = float(reference["do_not_go_below_without_contact_detection"])
    safe_max = float(reference["safe_retract_z"])
    responses: list[str] = []
    with serial.Serial(settings["port"], int(settings["baudrate"]), timeout=2) as ser:
        time.sleep(2)
        ser.write(b"M114\n")
        current_lines = _read_until_ok(ser, timeout_s=8.0)
        responses.extend(current_lines)
        current_z = _parse_z_from_lines(current_lines)
        if current_z is None:
            raise RuntimeError("Could not read current Z before manual move")
        delta = step_mm if direction_clean == "up" else -step_mm
        target_z = current_z + delta
        if target_z < safe_min or target_z > safe_max:
            raise ValueError(f"Manual Z target {target_z:.2f} outside safe approach range {safe_min:.2f}..{safe_max:.2f}")
        command = f"G1 Z{target_z:.2f} F300"
        for gcode in ("G90", command, "M400", "M114"):
            ser.write((gcode + "\n").encode("ascii", errors="replace"))
            lines = _read_until_ok(ser, timeout_s=60.0 if gcode in {command, "M400"} else 8.0)
            responses.extend(f"{gcode}: {line}" for line in lines)

    return ZManualMoveResult(
        success=True,
        command=command,
        responses=responses,
        target_z=target_z,
        message=f"Manual Z {direction_clean} step complete. Target Z={target_z:.2f}",
    )


def run_mk4s_z_safe_retract(*, execute: bool = False) -> ZManualMoveResult:
    reference = confirmed_approach_reference()
    safe_z = float(reference["safe_retract_z"])
    command = f"G1 Z{safe_z:.2f} F600"
    if not execute:
        return ZManualMoveResult(
            success=True,
            command=command,
            responses=[],
            target_z=safe_z,
            message="Preview only. No MK4S movement was sent.",
        )

    settings = get_motion_controller_settings()
    responses: list[str] = []
    with serial.Serial(settings["port"], int(settings["baudrate"]), timeout=2) as ser:
        time.sleep(2)
        for gcode in ("G90", command, "M400", "M114"):
            ser.write((gcode + "\n").encode("ascii", errors="replace"))
            lines = _read_until_ok(ser, timeout_s=60.0 if gcode in {command, "M400"} else 8.0)
            responses.extend(f"{gcode}: {line}" for line in lines)
    return ZManualMoveResult(
        success=True,
        command=command,
        responses=responses,
        target_z=safe_z,
        message=f"Z safe retract complete. Target Z={safe_z:.2f}",
    )

