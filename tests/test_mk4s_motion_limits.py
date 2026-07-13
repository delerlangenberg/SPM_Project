from core.web.mk4s_motion_limits import (
    estimate_raster_time_seconds,
    motion_limits_payload,
    validate_recommended_scan_speed,
)


def test_mk4s_motion_limits_payload_contains_axis_resolution():
    payload = motion_limits_payload()

    assert payload["x_build_mm"] == 250.0
    assert payload["y_build_mm"] == 210.0
    assert payload["z_build_mm"] == 220.0
    assert payload["machine"] == "Original Prusa MK4S scanner platform"
    assert payload["safe_center_x_mm"] == 125.0
    assert payload["safe_parking_z_mm"] == 120.0
    assert payload["x_default_max_feedrate_mm_s"] == 300.0
    assert payload["xy_command_resolution_um"] == 10.0
    assert payload["z_command_resolution_um"] == 2.5
    assert payload["recommended_z_manual_step_default_mm"] == 0.10
    assert "loadcell" in payload["loadcell_note"].lower()


def test_mk4s_motion_limits_scan_speed_validation():
    assert validate_recommended_scan_speed(5.0)[0] is True
    assert validate_recommended_scan_speed(50.0)[0] is False


def test_mk4s_raster_time_estimator():
    seconds = estimate_raster_time_seconds(
        x_min_mm=20.0,
        x_max_mm=80.0,
        y_lines=32,
        scan_speed_mm_s=5.0,
        overhead_per_line_s=0.25,
    )
    assert 390.0 < seconds < 395.0
