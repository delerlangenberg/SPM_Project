from core.system.hardware_initialized_profile import load_hardware_initialized_profile


def test_motion_limits_are_stored_from_firmware():
    profile = load_hardware_initialized_profile()
    limits = profile["hardware_initialized_profile"]["motion_limits"]

    assert limits["source"] == "Firmware M211 read-only query"
    assert limits["soft_endstops"] == "ON"
    assert limits["x_min"] == -1.00
    assert limits["x_max"] == 251.00
    assert limits["y_min"] == -4.00
    assert limits["y_max"] == 211.00
    assert limits["z_min"] == 0.00
    assert limits["z_max"] == 221.00


def test_phase8_visible_xy_motion_confirmed():
    profile = load_hardware_initialized_profile()
    motion = profile["hardware_initialized_profile"]["motion_limits"]["phase8_confirmed_motion"]

    assert motion["x_visible_move_5mm"] is True
    assert motion["y_visible_move_5mm"] is True
