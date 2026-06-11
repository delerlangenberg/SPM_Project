from core.system.hardware_startup_initializer import (
    READONLY_STARTUP_COMMANDS,
    HardwareStartupResult,
    StartupCommandResult,
)


def test_readonly_startup_commands_are_safe():
    assert READONLY_STARTUP_COMMANDS == ("M115", "M105", "M119")
    assert "G28" not in READONLY_STARTUP_COMMANDS
    assert "G1" not in READONLY_STARTUP_COMMANDS
    assert "M17" not in READONLY_STARTUP_COMMANDS


def test_startup_result_success_is_structured():
    result = HardwareStartupResult(
        success=True,
        port="COM5",
        baudrate=115200,
        timestamp="2026-06-11T17:50:00",
        command_results=[
            StartupCommandResult(
                command="M115",
                success=True,
                response_lines=["FIRMWARE_NAME:Prusa-Firmware-Buddy", "ok"],
            )
        ],
    )

    assert result.success is True
    assert result.port == "COM5"
    assert result.baudrate == 115200
    assert result.command_results[0].command == "M115"
