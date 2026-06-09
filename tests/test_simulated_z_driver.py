from core.z_control.z_driver_simulated import SimulatedZDriver


def test_simulated_z_driver_starts_at_zero():
    z = SimulatedZDriver()
    assert z.get_position() == 0.0


def test_simulated_z_driver_move_to_updates_position():
    z = SimulatedZDriver()
    z.move_to(1.5)
    assert z.get_position() == 1.5
