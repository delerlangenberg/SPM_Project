from core.education.config_loader import load_config
from core.system.hardware_profile import SPMHardwareProfile


def test_hardware_profile_distinguishes_spm_safe_and_firmware_limits():
    profile = SPMHardwareProfile.from_config(load_config())

    assert profile.x.spm_hint() == "SPM safe 20..80 mm"
    assert profile.x.firmware_hint() == "MK4S soft 0..250 mm"
    assert "SPM safe" in profile.axis_hint("X")
    assert "MK4S soft" in profile.axis_hint("X")
    assert profile.compact_axis_range("X") == "0-250"


def test_hardware_profile_contains_resolution_and_tuning_tips():
    profile = SPMHardwareProfile.from_config(load_config())

    assert "5 x 5" in profile.recommended_resolution
    assert "Higher resolution" in profile.resolution_tip
    assert "near 46..54 mm" in profile.scan_tuning_tip
    assert "Resolution: 3-250; start 3/5" in profile.scan_mode_limits_text("SIMULATED_SURFACE")
    assert "Official MK4S build volume: 250 x 210 x 220 mm" in profile.scan_mode_limits_text("SIMULATED_SURFACE")
    assert "Official maxima tested: X250, Y210, Z220" in profile.scan_mode_limits_text("SIMULATED_SURFACE")
