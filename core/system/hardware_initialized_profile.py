"""Load confirmed SPM hardware initialization settings."""

import json
import sys
from pathlib import Path


DEFAULT_PROFILE_PATH = Path("config/spm_hardware_initialized_profile.json")


def _resolve_profile_path(path: str | Path) -> Path:
    """Resolve project files both from source and from a PyInstaller bundle."""
    profile_path = Path(path)
    if profile_path.is_absolute() or profile_path.exists():
        return profile_path

    bundle_root = getattr(sys, "_MEIPASS", None)
    if bundle_root:
        bundled_path = Path(bundle_root) / profile_path
        if bundled_path.exists():
            return bundled_path

    return profile_path


def _validate_profile(profile: dict) -> None:
    """Reject unsafe or internally contradictory calibrated motion data."""
    try:
        root = profile["hardware_initialized_profile"]
        reference = root["z_approach_reference"]
        auto = reference["auto_step_approach_confirmed"]
        manual_contact_z = float(reference["manual_near_contact_z"])
        minimum_z = float(reference["do_not_go_below_without_contact_detection"])
        confirmed_stop_z = float(auto["stop_z"])
        start_z = float(auto["start_z"])
        retract_z = float(auto["safe_retract_z"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"Invalid hardware profile structure: {exc}") from exc

    if manual_contact_z != confirmed_stop_z:
        raise ValueError(
            "Unsafe Z calibration: manual_near_contact_z must match the "
            "confirmed auto-step stop_z"
        )
    if not minimum_z <= manual_contact_z < start_z <= retract_z:
        raise ValueError(
            "Unsafe Z calibration ordering: expected minimum_z <= contact_z "
            "< start_z <= safe_retract_z"
        )


def load_hardware_initialized_profile(path: str | Path = DEFAULT_PROFILE_PATH) -> dict:
    profile_path = _resolve_profile_path(path)

    if not profile_path.exists():
        raise FileNotFoundError(f"Hardware initialized profile not found: {profile_path}")

    profile = json.loads(profile_path.read_text(encoding="utf-8-sig"))
    _validate_profile(profile)
    return profile


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
