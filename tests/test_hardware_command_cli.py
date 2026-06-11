import subprocess
import sys


def run_cli(command: str):
    return subprocess.run(
        [sys.executable, "-m", "core.application.hardware_command_cli", command],
        capture_output=True,
        text=True,
        check=False,
    )


def test_hardware_command_cli_info():
    result = run_cli("INFO")

    assert result.returncode == 0
    assert "command=INFO" in result.stdout
    assert "success=True" in result.stdout
    assert "POWER=OFF" in result.stdout


def test_hardware_command_cli_power_on():
    result = run_cli("POWER_ON")

    assert result.returncode == 0
    assert "command=POWER_ON" in result.stdout
    assert "OK: POWER ON" in result.stdout


def test_hardware_command_cli_rejects_motion_command():
    result = run_cli("MOVE_X")

    assert result.returncode != 0
    assert "invalid choice" in result.stderr
