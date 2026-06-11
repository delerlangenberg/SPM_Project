from pathlib import Path

from core.hardware.hardware_command_bus import SimulatedHardwareCommandBus
from core.hardware.hardware_command_log import append_hardware_command_log


def test_append_hardware_command_log_creates_csv(tmp_path):
    bus = SimulatedHardwareCommandBus()
    result = bus.send("INFO")

    log_path = append_hardware_command_log(
        result,
        tmp_path / "hardware_command_log.csv",
    )

    content = Path(log_path).read_text(encoding="utf-8")

    assert "timestamp,command,success,response" in content
    assert "INFO" in content
    assert "POWER=OFF" in content


def test_append_hardware_command_log_appends_rows(tmp_path):
    bus = SimulatedHardwareCommandBus()
    log_file = tmp_path / "hardware_command_log.csv"

    append_hardware_command_log(bus.send("INFO"), log_file)
    append_hardware_command_log(bus.send("POWER_ON"), log_file)

    lines = log_file.read_text(encoding="utf-8").strip().splitlines()

    assert len(lines) == 3
    assert lines[0] == "timestamp,command,success,response"
    assert "INFO" in lines[1]
    assert "POWER_ON" in lines[2]
