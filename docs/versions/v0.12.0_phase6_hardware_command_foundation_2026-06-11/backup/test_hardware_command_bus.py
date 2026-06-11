from core.hardware.hardware_command_bus import SimulatedHardwareCommandBus


def test_power_on_off_info_exchange():
    bus = SimulatedHardwareCommandBus()

    info_before = bus.send("INFO")
    assert info_before.success is True
    assert "POWER=OFF" in info_before.response

    power_on = bus.send("POWER_ON")
    assert power_on.success is True
    assert power_on.response == "OK: POWER ON"

    info_after = bus.send("INFO")
    assert "POWER=ON" in info_after.response

    power_off = bus.send("POWER_OFF")
    assert power_off.success is True
    assert power_off.response == "OK: POWER OFF"


def test_safe_stop_forces_power_off():
    bus = SimulatedHardwareCommandBus()
    bus.send("POWER_ON")

    result = bus.send("SAFE_STOP")

    assert result.success is True
    assert bus.powered_on is False
    assert "SAFE STOP" in result.response


def test_unknown_command_fails_safely():
    bus = SimulatedHardwareCommandBus()

    result = bus.send("MOVE_X")

    assert result.success is False
    assert "UNKNOWN COMMAND" in result.response
    assert bus.powered_on is False
