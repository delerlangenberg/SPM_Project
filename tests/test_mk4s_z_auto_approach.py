from core.system.mk4s_z_auto_approach import planned_auto_approach_commands, run_mk4s_z_auto_approach


def test_planned_auto_approach_uses_confirmed_phase9_reference():
    commands = planned_auto_approach_commands()

    assert "G1 Z120.00 F600" in commands
    assert "G1 X125.00 Y105.00 F1200" in commands
    assert "G1 Z56.00 F60" in commands
    assert commands[-1] == "M114"


def test_auto_approach_preview_does_not_execute_motion():
    result = run_mk4s_z_auto_approach(execute=False)

    assert result.success is True
    assert result.dry_run is True
    assert result.final_z == 56.0
    assert "No MK4S movement" in result.message


def test_auto_approach_setpoint_stops_above_surface_reference():
    commands = planned_auto_approach_commands(setpoint_distance_mm=1.5)
    result = run_mk4s_z_auto_approach(execute=False, setpoint_distance_mm=1.5)

    assert "G1 Z57.50 F60" in commands
    assert result.final_z == 57.5
