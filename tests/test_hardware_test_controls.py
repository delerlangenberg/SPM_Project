import subprocess
import sys

import pytest

from core.system.hardware_test_controls import (
    HARDWARE_TEST_ACTIONS,
    HardwareTestResult,
    SAFE_CENTER_X,
    SAFE_CENTER_Y,
    SAFE_RETRACT_Z,
    append_hardware_test_log,
    plan_hardware_test_action,
    run_hardware_test_action,
)


def test_hardware_test_actions_are_explicit():
    assert HARDWARE_TEST_ACTIONS == (
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


def test_safe_center_retracts_z_before_xy_motion():
    plan = plan_hardware_test_action("SAFE_CENTER")

    assert plan.moves_hardware is True
    assert plan.commands[0] == f"G1 Z{SAFE_RETRACT_Z:.2f} F300"
    assert plan.commands[2] == f"G1 X{SAFE_CENTER_X:.2f} Y{SAFE_CENTER_Y:.2f} F600"


def test_read_position_is_no_motion_plan():
    plan = plan_hardware_test_action("READ_POSITION")

    assert plan.moves_hardware is False
    assert plan.commands == ["M114"]


def test_step_plan_uses_current_position_and_limits():
    plan = plan_hardware_test_action("X_STEP_PLUS", current_position={"x": 125.0, "y": 105.0, "z": 120.0}, step_mm=5)

    assert plan.commands[0] == "G1 X130.00 F600"


def test_step_plan_rejects_out_of_limit_target():
    with pytest.raises(ValueError):
        plan_hardware_test_action("Z_STEP_UP", current_position={"x": 125.0, "y": 105.0, "z": 220.0}, step_mm=5)


def test_run_hardware_test_action_defaults_to_dry_run():
    result = run_hardware_test_action("SAFE_RETRACT")

    assert result.success is True
    assert result.before_position == {}
    assert result.after_position == {}
    assert "DRY RUN ONLY" in result.response


def test_hardware_test_control_cli_defaults_to_no_motion_dry_run():
    result = subprocess.run(
        [sys.executable, "-m", "core.application.hardware_test_control_cli", "SAFE_CENTER"],
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )

    assert result.returncode == 0
    assert "DRY RUN ONLY" in result.stdout
    assert "G1 Z120.00 F300" in result.stdout
    assert "G1 X125.00 Y105.00 F600" in result.stdout


def test_hardware_test_log_flattens_newlines(tmp_path):
    result = HardwareTestResult(
        action="SAFE_CENTER",
        success=True,
        commands=["G1 Z120.00 F300", "M400"],
        before_position={},
        after_position={},
        response="line one\nline two",
        timestamp="2026-06-12T13:05:00",
    )

    log_path = append_hardware_test_log(result, tmp_path / "hardware_test.csv")
    text = log_path.read_text(encoding="utf-8")

    assert "line one line two" in text
    assert "line one\nline two" not in text
