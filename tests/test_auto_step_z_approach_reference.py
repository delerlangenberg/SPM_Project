from core.system.hardware_initialized_profile import load_hardware_initialized_profile


def test_auto_step_z_approach_reference_is_stored():
    profile = load_hardware_initialized_profile()
    auto = profile["hardware_initialized_profile"]["z_approach_reference"]["auto_step_approach_confirmed"]

    assert auto["method"] == "software-controlled step approach"
    assert auto["x"] == 125.00
    assert auto["y"] == 105.00
    assert auto["start_z"] == 120.00
    assert auto["stop_z"] == 56.00
    assert auto["contact_observed_by_user"] is True
    assert auto["safe_retract_z"] == 120.00
    assert auto["result"] == "success"
