from core.application.cli_scan_launcher import (
    build_motion_limits_from_config,
    build_scan_profile_from_config,
)
from core.education.config_loader import load_config
from core.education.scan_profile import validate_scan_profile


def test_cli_builds_valid_scan_profile_from_config():
    config = load_config()

    profile = build_scan_profile_from_config(config, mode="SIMULATED_SURFACE")
    limits = build_motion_limits_from_config(config)

    validate_scan_profile(profile, limits)

    assert profile.x_min == 46
    assert profile.x_max == 54
    assert profile.y_min == 46
    assert profile.y_max == 54
    assert profile.z == 20
    assert profile.x_resolution == 5
    assert profile.y_resolution == 5
    assert profile.mode == "SIMULATED_SURFACE"


def test_cli_builds_motion_limits_from_config():
    config = load_config()

    limits = build_motion_limits_from_config(config)

    assert limits.x_min == 0
    assert limits.x_max == 250
    assert limits.y_min == 0
    assert limits.y_max == 210
    assert limits.z_min == 0
    assert limits.z_max == 220

def test_run_verified_hardware_raster_uses_verified_script(monkeypatch):
    calls = {}

    def fake_run(command, check):
        calls["command"] = command
        calls["check"] = check

        class Result:
            returncode = 0

        return Result()

    monkeypatch.setattr(
        "core.application.cli_scan_launcher.subprocess.run",
        fake_run,
    )

    from core.application.cli_scan_launcher import run_verified_hardware_raster
    from core.education.scan_profile import ScanProfile

    profile = ScanProfile(
        x_min=48,
        x_max=52,
        y_min=48,
        y_max=52,
        z=20,
        x_resolution=3,
        y_resolution=3,
        feedrate_xy=1200,
        feedrate_z=300,
        mode="SIMULATED_SURFACE",
    )

    exit_code = run_verified_hardware_raster(profile)

    assert exit_code == 0
    assert calls["command"][1] == "tools/run_configured_raster_scan.py"
    assert "--feedrate-xy" in calls["command"]
    assert "--feedrate-z" in calls["command"]
    assert calls["check"] is False


def test_run_verified_software_raster_uses_dry_run_flag(monkeypatch):
    calls = {}

    def fake_run(command, check):
        calls["command"] = command
        calls["check"] = check

        class Result:
            returncode = 0

        return Result()

    monkeypatch.setattr(
        "core.application.cli_scan_launcher.subprocess.run",
        fake_run,
    )

    from core.application.cli_scan_launcher import run_verified_software_raster
    from core.education.scan_profile import ScanProfile

    profile = ScanProfile(
        x_min=48,
        x_max=52,
        y_min=48,
        y_max=52,
        z=20,
        x_resolution=3,
        y_resolution=3,
        feedrate_xy=1200,
        feedrate_z=300,
        mode="SIMULATED_SURFACE",
    )

    exit_code = run_verified_software_raster(profile, "data/dry_run.csv")

    assert exit_code == 0
    assert calls["command"][1] == "tools/run_configured_raster_scan.py"
    assert "--dry-run" in calls["command"]
    assert "--feedrate-xy" in calls["command"]
    assert "--feedrate-z" in calls["command"]
    assert calls["check"] is False

def test_cli_overrides_scan_profile_values():
    import argparse

    from core.application.cli_scan_launcher import apply_cli_overrides
    from core.education.scan_profile import ScanProfile

    profile = ScanProfile(
        x_min=46,
        x_max=54,
        y_min=46,
        y_max=54,
        z=20,
        x_resolution=5,
        y_resolution=5,
        feedrate_xy=1200,
        feedrate_z=300,
        mode="SIMULATED_SURFACE",
    )

    args = argparse.Namespace(
        x_min=48,
        x_max=52,
        y_min=48,
        y_max=52,
        z=20,
        x_resolution=3,
        y_resolution=3,
        feedrate_xy=900,
        feedrate_z=150,
    )

    updated = apply_cli_overrides(profile, args)

    assert updated.x_min == 48
    assert updated.x_max == 52
    assert updated.y_min == 48
    assert updated.y_max == 52
    assert updated.z == 20
    assert updated.x_resolution == 3
    assert updated.y_resolution == 3
    assert updated.feedrate_xy == 900
    assert updated.feedrate_z == 150
    assert updated.mode == "SIMULATED_SURFACE"


def test_cli_overrides_keep_original_values_when_none():
    import argparse

    from core.application.cli_scan_launcher import apply_cli_overrides
    from core.education.scan_profile import ScanProfile

    profile = ScanProfile(
        x_min=46,
        x_max=54,
        y_min=46,
        y_max=54,
        z=20,
        x_resolution=5,
        y_resolution=5,
        feedrate_xy=1200,
        feedrate_z=300,
        mode="SIMULATED_SURFACE",
    )

    args = argparse.Namespace(
        x_min=None,
        x_max=None,
        y_min=None,
        y_max=None,
        z=None,
        x_resolution=None,
        y_resolution=None,
    )

    updated = apply_cli_overrides(profile, args)

    assert updated == profile

def test_cli_validation_failure_returns_clean_error(capsys):
    from core.application import cli_scan_launcher

    original_argv = cli_scan_launcher.sys.argv

    cli_scan_launcher.sys.argv = [
        "cli_scan_launcher.py",
        "--dry-run",
        "--x-min",
        "-10",
        "--x-max",
        "52",
    ]

    try:
        try:
            cli_scan_launcher.main()
        except SystemExit as error:
            assert error.code == 1

        output = capsys.readouterr().out
        assert "Validation: FAIL" in output
        assert "Reason: x_min is outside motion limits" in output

    finally:
        cli_scan_launcher.sys.argv = original_argv
