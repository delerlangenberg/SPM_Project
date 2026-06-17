from dataclasses import dataclass


@dataclass(frozen=True)
class MotionLimits:
    x_min: float
    x_max: float
    y_min: float
    y_max: float
    z_min: float
    z_max: float


@dataclass(frozen=True)
class ScanProfile:
    x_min: float
    x_max: float
    y_min: float
    y_max: float
    z: float
    x_resolution: int
    y_resolution: int
    feedrate_xy: float
    feedrate_z: float
    mode: str = "SIMULATED_SURFACE"


VALID_SCAN_MODES = {
    "SIMULATED_SURFACE",
    "CONTACT_PROBE",
    "AFM_CONTACT",
    "STM_DEMO",
}


MAX_SCAN_RESOLUTION = 250


def validate_scan_profile(profile: ScanProfile, limits: MotionLimits) -> None:
    if profile.mode not in VALID_SCAN_MODES:
        raise ValueError(f"Invalid scan mode: {profile.mode}")

    if profile.x_min >= profile.x_max:
        raise ValueError("x_min must be smaller than x_max")

    if profile.y_min >= profile.y_max:
        raise ValueError("y_min must be smaller than y_max")

    if profile.x_resolution < 2:
        raise ValueError("x_resolution must be at least 2")

    if profile.y_resolution < 2:
        raise ValueError("y_resolution must be at least 2")

    if profile.x_resolution > MAX_SCAN_RESOLUTION:
        raise ValueError(f"x_resolution must be at most {MAX_SCAN_RESOLUTION}")

    if profile.y_resolution > MAX_SCAN_RESOLUTION:
        raise ValueError(f"y_resolution must be at most {MAX_SCAN_RESOLUTION}")

    if not (limits.x_min <= profile.x_min <= limits.x_max):
        raise ValueError("x_min is outside motion limits")

    if not (limits.x_min <= profile.x_max <= limits.x_max):
        raise ValueError("x_max is outside motion limits")

    if not (limits.y_min <= profile.y_min <= limits.y_max):
        raise ValueError("y_min is outside motion limits")

    if not (limits.y_min <= profile.y_max <= limits.y_max):
        raise ValueError("y_max is outside motion limits")

    if not (limits.z_min <= profile.z <= limits.z_max):
        raise ValueError("z is outside motion limits")

    if profile.feedrate_xy <= 0:
        raise ValueError("feedrate_xy must be positive")

    if profile.feedrate_z <= 0:
        raise ValueError("feedrate_z must be positive")
