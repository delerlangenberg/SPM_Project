from core.system.hardware_initialized_profile import load_hardware_initialized_profile


def test_y_axis_direction_observation_is_stored():
    profile = load_hardware_initialized_profile()
    direction = profile["hardware_initialized_profile"]["motion_limits"]["axis_direction_observation"]

    assert direction["y_axis"]["confirmed_by_user"] is True
    assert direction["y_axis"]["software_coordinate_change"] == "Y 1.00 -> Y 211.00 -> Y 1.00"
    assert "forward" in direction["y_axis"]["observed_physical_motion"]
    assert "backward" in direction["y_axis"]["observed_physical_motion"]
