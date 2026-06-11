from core.system.hardware_initialized_profile import (
    get_motion_controller_settings,
    initialization_allows_only_readonly_checks,
    load_hardware_initialized_profile,
)


def test_load_hardware_initialized_profile():
    profile = load_hardware_initialized_profile()

    assert profile["hardware_initialized_profile"]["confirmed"] is True
    assert profile["hardware_initialized_profile"]["motion_controller"]["port"] == "COM5"
    assert profile["hardware_initialized_profile"]["motion_controller"]["baudrate"] == 115200


def test_motion_controller_identity_is_prusa_mk4():
    controller = get_motion_controller_settings()

    assert controller["machine_type"] == "Prusa-MK4"
    assert controller["firmware_name"] == "Prusa-Firmware-Buddy 6.2.4+8909"
    assert controller["usb_vid"] == "2C99"
    assert controller["usb_pid"] == "000D"


def test_initialization_is_readonly_safe():
    assert initialization_allows_only_readonly_checks() is True
