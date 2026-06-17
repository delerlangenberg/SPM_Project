import subprocess
import sys

import pytest

from core.system.hardware_information_exchange import (
    READONLY_HARDWARE_ACTIONS,
    action_commands,
    assert_readonly_command,
    run_with_transport,
)


def test_readonly_hardware_actions_are_information_only():
    assert READONLY_HARDWARE_ACTIONS == {
        "IDENTITY": "M115",
        "TEMPERATURE": "M105",
        "ENDSTOPS": "M119",
        "POSITION": "M114",
    }
    for command in READONLY_HARDWARE_ACTIONS.values():
        assert_readonly_command(command)


def test_motion_commands_are_rejected_from_information_layer():
    for command in ["G1 X125", "G28", "M17", "M112"]:
        with pytest.raises(ValueError):
            assert_readonly_command(command)


def test_action_commands_expands_all_in_safe_order():
    assert action_commands("ALL") == [
        ("IDENTITY", "M115"),
        ("TEMPERATURE", "M105"),
        ("ENDSTOPS", "M119"),
        ("POSITION", "M114"),
    ]


def test_run_with_transport_returns_structured_results():
    sent = []

    def fake_send(command: str) -> list[str]:
        sent.append(command)
        return [f"response for {command}", "ok"]

    results = run_with_transport("POSITION", fake_send)

    assert sent == ["M114"]
    assert len(results) == 1
    assert results[0].action == "POSITION"
    assert results[0].command == "M114"
    assert results[0].success is True


def test_hardware_information_cli_defaults_to_no_serial_dry_run():
    result = subprocess.run(
        [sys.executable, "-m", "core.application.hardware_information_cli", "ALL"],
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )

    assert result.returncode == 0
    assert "DRY RUN ONLY" in result.stdout
    assert "plan: IDENTITY -> M115" in result.stdout
    assert "plan: POSITION -> M114" in result.stdout
