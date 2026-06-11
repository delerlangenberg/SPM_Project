"""Load confirmed SPM hardware initialization settings."""

import json
from pathlib import Path


DEFAULT_PROFILE_PATH = Path("config/spm_hardware_initialized_profile.json")


def load_hardware_initialized_profile(path: str | Path = DEFAULT_PROFILE_PATH) -> dict:
    profile_path = Path(path)

    if not profile_path.exists():
        raise FileNotFoundError(f"Hardware initialized profile not found: {profile_path}")

    return json.loads(profile_path.read_text(encoding="utf-8-sig"))


def get_motion_controller_settings(path: str | Path = DEFAULT_PROFILE_PATH) -> dict:
    profile = load_hardware_initialized_profile(path)
    return profile["hardware_initialized_profile"]["motion_controller"]


def initialization_allows_only_readonly_checks(path: str | Path = DEFAULT_PROFILE_PATH) -> bool:
    profile = load_hardware_initialized_profile(path)
    rules = profile["hardware_initialized_profile"]["safety_rules"]

    return (
        rules["startup_allowed"] is True
        and rules["movement_allowed_during_initialization"] is False
        and rules["homing_allowed_during_initialization"] is False
        and rules["scan_allowed_during_initialization"] is False
        and rules["z_approach_allowed_during_initialization"] is False
    )
