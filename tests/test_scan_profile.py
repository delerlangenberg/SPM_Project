import pytest

from core.education.scan_profile import (
    MotionLimits,
    ScanProfile,
    validate_scan_profile,
)


def limits():
    return MotionLimits(
        x_min=20,
        x_max=80,
        y_min=20,
        y_max=80,
        z_min=5,
        z_max=50,
    )


def valid_profile():
    return ScanProfile(
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


def test_valid_scan_profile_passes():
    validate_scan_profile(valid_profile(), limits())


@pytest.mark.parametrize(
    "field,value",
    [
        ("x_min", 10),
        ("x_max", 90),
        ("y_min", 10),
        ("y_max", 90),
        ("z", 100),
        ("x_resolution", 1),
        ("y_resolution", 1),
        ("feedrate_xy", 0),
        ("feedrate_z", 0),
        ("mode", "BAD_MODE"),
    ],
)
def test_invalid_scan_profile_fails(field, value):
    profile_data = valid_profile().__dict__.copy()
    profile_data[field] = value

    bad_profile = ScanProfile(**profile_data)

    with pytest.raises(ValueError):
        validate_scan_profile(bad_profile, limits())


def test_x_min_must_be_smaller_than_x_max():
    profile_data = valid_profile().__dict__.copy()
    profile_data["x_min"] = 54
    profile_data["x_max"] = 46

    with pytest.raises(ValueError):
        validate_scan_profile(ScanProfile(**profile_data), limits())


def test_y_min_must_be_smaller_than_y_max():
    profile_data = valid_profile().__dict__.copy()
    profile_data["y_min"] = 54
    profile_data["y_max"] = 46

    with pytest.raises(ValueError):
        validate_scan_profile(ScanProfile(**profile_data), limits())
