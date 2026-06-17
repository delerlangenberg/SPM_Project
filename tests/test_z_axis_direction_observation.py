from core.system.hardware_initialized_profile import load_hardware_initialized_profile


def test_z_axis_direction_observation_is_stored():
    profile = load_hardware_initialized_profile()
    direction = profile["hardware_initialized_profile"]["motion_limits"]["axis_direction_observation"]

    assert direction["z_axis"]["confirmed_by_user"] is True
    assert direction["z_axis"]["software_coordinate_change"] == "Z 100.00 -> Z 120.00 -> Z 100.00"
    assert "up" in direction["z_axis"]["observed_physical_motion"]
    assert "down" in direction["z_axis"]["observed_physical_motion"]
