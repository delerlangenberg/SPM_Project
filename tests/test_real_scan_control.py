from core.web.real_scan_control import (
    clear_real_scan_pause,
    FoilTapConfig,
    RealScanPoint,
    _m119_contact_detected,
    _tap_z_values,
    real_scan_paused,
    real_scan_plan,
    request_real_scan_pause,
    validate_real_scan_profile,
)
from pathlib import Path
from core.web.spm_scan_simulation import WebScanProfile


def test_real_scan_plan_defaults_to_constant_z_raster():
    profile = WebScanProfile(x_min=75, x_max=175, y_min=55, y_max=155, x_points=10, y_points=1, z_setpoint=100, scan_direction="X-")
    plan = real_scan_plan(profile)

    assert plan["mode"] == "constant_z_real_m114_raster"
    assert plan["point_count"] == 10
    assert plan["scan_direction"] == "X-"
    assert plan["execution_gate"] == "SPM_WEB_ALLOW_REAL_SCAN=1"


def test_real_scan_validation_blocks_outside_xy_limits():
    profile = WebScanProfile(x_min=-2, x_max=175, y_min=55, y_max=155, x_points=10, y_points=1, z_setpoint=100)

    try:
        validate_real_scan_profile(profile)
    except ValueError as exc:
        assert "X scan range" in str(exc)
    else:
        raise AssertionError("validate_real_scan_profile should block unsafe X range")


def test_real_scan_pause_flag_round_trip():
    clear_real_scan_pause()
    assert real_scan_paused() is False


def test_real_scan_point_carries_exact_z_feedback_fields():
    point = RealScanPoint(
        point_index=0,
        line_index=0,
        x=125.0,
        y=105.0,
        z_feedback=100.0,
        measured_z=100.0,
        commanded_z=100.0,
        surface_height=0.0,
        feedback_error=0.0,
        feedback_source="M114_exact_z_readback",
    )

    assert point.z_feedback == point.measured_z
    assert point.feedback_source == "M114_exact_z_readback"

    request_real_scan_pause()
    assert real_scan_paused() is True

    clear_real_scan_pause()
    assert real_scan_paused() is False


def test_foil_tap_config_generates_descending_z_path():
    config = FoilTapConfig(z_setpoint_mm=148.0, tapping_range_mm=2.0, tap_step_fast_mm=1.0, tap_step_fine_mm=0.25, fine_zone_mm=1.0)
    path = _tap_z_values(config)

    assert path[0] == 149.0
    assert path[-1] == 148.0
    assert all(a > b for a, b in zip(path, path[1:]))
    assert config.abort_on_no_contact is True


def test_foil_tap_defaults_are_table_referenced():
    config = FoilTapConfig()

    assert config.table_z_mm == 0.0
    assert config.z_setpoint_mm == 0.0
    assert config.tapping_range_mm == 20.0
    assert config.approach_speed_mm_s == 2.0
    assert config.tap_min_z_mm == 0.0
    assert config.tap_start_z_mm > config.table_z_mm
    assert config.full_retract_z_mm > config.tap_start_z_mm


def test_m119_contact_parser_detects_triggered_z_min():
    assert _m119_contact_detected(["Reporting endstop status", "z_min: open", "ok"]) is False
    assert _m119_contact_detected(["Reporting endstop status", "z_min: TRIGGERED", "ok"]) is True


def test_foil_tap_backend_full_retracts_and_explains_no_contact():
    source = Path("core/web/real_scan_control.py").read_text(encoding="utf-8")

    assert "retract_z = config.full_retract_z_mm" in source
    assert "configured Z search lower limit" in source
    assert "Lower the Z setpoint/search limit below the expected surface height" in source
    assert "FOIL TAP: scanner pre-positioned to XY minimum before first approach." in source
