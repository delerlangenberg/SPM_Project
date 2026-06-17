from core.application.workstation_status import WorkstationStatus
from core.education.config_loader import load_config


def test_workstation_status_starts_safe_from_config():
    status = WorkstationStatus.from_config(load_config())

    assert status.machine_port == "COM5"
    assert status.system_check_passed is False
    assert status.real_motion_enabled is False
    assert "real motion disabled" in status.safety_summary().lower()


def test_workstation_status_blocks_real_motion_before_system_check():
    status = WorkstationStatus.from_config(load_config())

    try:
        status.enable_real_motion()
    except RuntimeError as error:
        assert "Run system check" in str(error)
    else:
        raise AssertionError("real motion enabled without a system check")


def test_workstation_status_tracks_scan_output():
    status = WorkstationStatus.from_config(load_config())

    status.record_scan_output("data/out.csv", "data/out.png", 25)

    assert status.acquisition_points == 25
    assert "25 raster points loaded" in status.acquisition_summary()
    assert "data/out.png" in status.output_summary()


def test_validation_failure_does_not_clear_completed_initialization():
    status = WorkstationStatus.from_config(load_config())

    status.record_system_check_pass()
    status.record_validation_fail("bad scan range")

    assert status.system_check_passed is True
    assert status.real_motion_enabled is False
    assert status.scan_profile_valid is False
