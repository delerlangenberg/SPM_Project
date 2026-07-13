from core.system import mk4s_z_auto_approach as approach


def fake_reference(manual_near_contact_z: float = 72.0):
    return {
        "manual_near_contact_z": manual_near_contact_z,
        "do_not_go_below_without_contact_detection": 40.0,
        "auto_step_approach_confirmed": {
            "x": 125.0,
            "y": 105.0,
            "start_z": 120.0,
            "feedrate": 300.0,
            "safe_retract_z": 120.0,
        },
    }


def z_moves(commands):
    values = []
    for command in commands:
        if command.startswith("G1 Z"):
            z_part = command.split()[1]
            values.append(float(z_part.replace("Z", "")))
    return values


def test_auto_approach_does_not_force_z60_when_stop_z_is_above_60(monkeypatch):
    monkeypatch.setattr(
        approach,
        "confirmed_approach_reference",
        lambda: fake_reference(manual_near_contact_z=72.0),
    )

    commands = approach.planned_auto_approach_commands(
        setpoint_distance_mm=10.0,
        retract_after=False,
    )

    moves = z_moves(commands)

    assert 60.0 not in moves
    assert min(moves) == 82.0
    assert moves[-1] == 82.0


def test_auto_approach_still_allows_z60_when_requested_stop_is_60_or_lower(monkeypatch):
    monkeypatch.setattr(
        approach,
        "confirmed_approach_reference",
        lambda: fake_reference(manual_near_contact_z=50.0),
    )

    commands = approach.planned_auto_approach_commands(
        setpoint_distance_mm=10.0,
        retract_after=False,
    )

    moves = z_moves(commands)

    assert 60.0 in moves
    assert min(moves) == 60.0
    assert moves[-1] == 60.0


def test_setpoint_move_uses_fast_coarse_steps_then_fine_final_steps():
    path = approach._planned_z_path(120.0, 57.0)

    assert path[0] == 63.3
    assert path[-1] == 57.0
    assert path == [63.3, 62.3, 61.3, 60.3, 59.3, 58.3, 57.3, 57.0]


def test_setpoint_move_fast_phase_is_ninety_percent_of_travel():
    path = approach._planned_z_path(150.0, 100.0)

    assert path[0] == 105.0
    assert path[-1] == 100.0
