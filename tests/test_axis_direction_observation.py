from core.system.hardware_initialized_profile import load_hardware_initialized_profile


def test_x_axis_direction_observation_is_stored():
    profile = load_hardware_initialized_profile()
    direction = profile["hardware_initialized_profile"]["motion_limits"]["axis_direction_observation"]

    assert direction["x_axis"]["confirmed_by_user"] is True
    assert direction["x_axis"]["software_coordinate_change"] == "X 1.00 -> X 251.00 -> X 1.00"
    assert "right-to-left" in direction["x_axis"]["observed_physical_motion"]
