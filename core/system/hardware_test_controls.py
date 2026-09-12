"""Supervised hardware test controls for the MK4S scanner layer.

Dry-run planning is the default. Real movement requires an explicit CLI flag.
This module is intended to become the backend for future GUI hardware-test
buttons after the command behavior is verified phase by phase.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from core.motion.prusa_gcode_backend import PrusaGcodeBackend
from core.system.hardware_initialized_profile import get_motion_controller_settings


HARDWARE_TEST_ACTIONS = (
    "READ_POSITION",
    "SAFE_RETRACT",
    "SAFE_CENTER",
    "X_STEP_PLUS",
    "X_STEP_MINUS",
    "Y_STEP_PLUS",
    "Y_STEP_MINUS",
    "Z_STEP_UP",
    "Z_STEP_DOWN",
)

SAFE_CENTER_X = 125.0
SAFE_CENTER_Y = 105.0
SAFE_RETRACT_Z = 120.0
DEFAULT_STEP_MM = 5.0
DEFAULT_XY_FEEDRATE = 600.0
DEFAULT_Z_FEEDRATE = 300.0
LIMITS = {
    "x": (-1.0, 251.0),
    "y": (-4.0, 211.0),
    "z": (0.0, 221.0),
}


@dataclass(frozen=True)
class HardwareTestPlan:
    action: str
    commands: list[str]
    moves_hardware: bool
    safety_note: str


@dataclass(frozen=True)
class HardwareTestResult:
    action: str
    success: bool
    commands: list[str]
    before_position: dict[str, float]
    after_position: dict[str, float]
    response: str
    timestamp: str


def assert_in_limits(axis: str, value: float) -> None:
    low, high = LIMITS[axis]
    if value < low or value > high:
        raise ValueError(f"{axis.upper()} target {value} outside confirmed limits [{low}, {high}]")


def plan_hardware_test_action(
    action: str,
    *,
    current_position: dict[str, float] | None = None,
    step_mm: float = DEFAULT_STEP_MM,
) -> HardwareTestPlan:
    action_clean = action.strip().upper()
    if action_clean not in HARDWARE_TEST_ACTIONS:
        raise ValueError(f"Unknown hardware test action {action!r}")
    if step_mm <= 0:
        raise ValueError("step_mm must be positive")

    current_position = current_position or {"x": SAFE_CENTER_X, "y": SAFE_CENTER_Y, "z": SAFE_RETRACT_Z}

    if action_clean == "READ_POSITION":
        return HardwareTestPlan(action_clean, ["M114"], False, "Read-only XYZ position query.")

    if action_clean == "SAFE_RETRACT":
        return HardwareTestPlan(
            action_clean,
            [f"G1 Z{SAFE_RETRACT_Z:.2f} F{DEFAULT_Z_FEEDRATE:.0f}", "M400", "M114"],
            True,
            "Retract Z to the confirmed safe height.",
        )

    if action_clean == "SAFE_CENTER":
        return HardwareTestPlan(
            action_clean,
            [
                f"G1 Z{SAFE_RETRACT_Z:.2f} F{DEFAULT_Z_FEEDRATE:.0f}",
                "M400",
                f"G1 X{SAFE_CENTER_X:.2f} Y{SAFE_CENTER_Y:.2f} F{DEFAULT_XY_FEEDRATE:.0f}",
                "M400",
                "M114",
            ],
            True,
            "Retract Z first, then return XY to foam center.",
        )

    axis_by_action = {
        "X_STEP_PLUS": ("x", step_mm, DEFAULT_XY_FEEDRATE),
        "X_STEP_MINUS": ("x", -step_mm, DEFAULT_XY_FEEDRATE),
        "Y_STEP_PLUS": ("y", step_mm, DEFAULT_XY_FEEDRATE),
        "Y_STEP_MINUS": ("y", -step_mm, DEFAULT_XY_FEEDRATE),
        "Z_STEP_UP": ("z", step_mm, DEFAULT_Z_FEEDRATE),
        "Z_STEP_DOWN": ("z", -step_mm, DEFAULT_Z_FEEDRATE),
    }
    axis, delta, feedrate = axis_by_action[action_clean]
    target = float(current_position.get(axis, {"x": SAFE_CENTER_X, "y": SAFE_CENTER_Y, "z": SAFE_RETRACT_Z}[axis])) + delta
    assert_in_limits(axis, target)
    return HardwareTestPlan(
        action_clean,
        [f"G1 {axis.upper()}{target:.2f} F{feedrate:.0f}", "M400", "M114"],
        True,
        f"Move {axis.upper()} by {delta:+.2f} mm from current readback.",
    )


def append_hardware_test_log(
    result: HardwareTestResult,
    log_path: str | Path = "logs/hardware_test_control_log.csv",
) -> Path:
    def csv_cell(value: object) -> str:
        return str(value).replace("\r", " ").replace("\n", " ").replace('"', '""')

    path = Path(log_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    new_file = not path.exists()
    with path.open("a", encoding="utf-8", newline="") as handle:
        if new_file:
            handle.write("timestamp,action,success,commands,before_position,after_position,response\n")
        commands = csv_cell(" | ".join(result.commands))
        before = csv_cell(result.before_position)
        after = csv_cell(result.after_position)
        response = csv_cell(result.response)
        handle.write(
            f'{result.timestamp},{result.action},{result.success},"{commands}","{before}","{after}","{response}"\n'
        )
    return path


def run_hardware_test_action(
    action: str,
    *,
    step_mm: float = DEFAULT_STEP_MM,
    execute: bool = False,
) -> HardwareTestResult:
    timestamp = datetime.now().isoformat(timespec="seconds")
    if not execute:
        plan = plan_hardware_test_action(action, step_mm=step_mm)
        return HardwareTestResult(
            action=plan.action,
            success=True,
            commands=plan.commands,
            before_position={},
            after_position={},
            response=f"DRY RUN ONLY: {plan.safety_note}",
            timestamp=timestamp,
        )

    settings = get_motion_controller_settings()
    backend = PrusaGcodeBackend(
        port=settings["port"],
        baudrate=int(settings["baudrate"]),
        timeout=0.5,
        auto_detect_port=False,
        x_limits=LIMITS["x"],
        y_limits=LIMITS["y"],
        z_limits=LIMITS["z"],
    )
    commands: list[str] = []
    before_position: dict[str, float] = {}
    after_position: dict[str, float] = {}
    try:
        backend.connect()
        before_state = backend.get_state()
        before_position = dict(before_state.get("position", {}))
        plan = plan_hardware_test_action(action, current_position=before_position, step_mm=step_mm)
        commands = plan.commands

        if plan.action == "READ_POSITION":
            after_position = before_position
        elif plan.action == "SAFE_RETRACT":
            backend.move_to(z=SAFE_RETRACT_Z, feedrate=DEFAULT_Z_FEEDRATE)
            backend.send_gcode("M400", timeout=60.0)
            after_position = dict(backend.get_state().get("position", {}))
        elif plan.action == "SAFE_CENTER":
            backend.move_to(z=SAFE_RETRACT_Z, feedrate=DEFAULT_Z_FEEDRATE)
            backend.send_gcode("M400", timeout=60.0)
            backend.move_to(x=SAFE_CENTER_X, y=SAFE_CENTER_Y, feedrate=DEFAULT_XY_FEEDRATE)
            backend.send_gcode("M400", timeout=60.0)
            after_position = dict(backend.get_state().get("position", {}))
        else:
            target_command = plan.commands[0]
            axis = target_command.split()[1][0].lower()
            value = float(target_command.split()[1][1:])
            kwargs = {axis: value, "feedrate": DEFAULT_Z_FEEDRATE if axis == "z" else DEFAULT_XY_FEEDRATE}
            backend.move_to(**kwargs)
            backend.send_gcode("M400", timeout=60.0)
            after_position = dict(backend.get_state().get("position", {}))

        return HardwareTestResult(
            action=plan.action,
            success=True,
            commands=commands,
            before_position=before_position,
            after_position=after_position,
            response=plan.safety_note,
            timestamp=timestamp,
        )
    except Exception as error:
        return HardwareTestResult(
            action=action.strip().upper(),
            success=False,
            commands=commands,
            before_position=before_position,
            after_position=after_position,
            response=repr(error),
            timestamp=timestamp,
        )
    finally:
        backend.disconnect()
