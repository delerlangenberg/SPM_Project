import json
from pathlib import Path


DEFAULT_CONFIG_PATH = Path("config/spm_mk4s_config.json")


def load_config(path=DEFAULT_CONFIG_PATH):
    """Load SPM MK4S JSON configuration."""
    path = Path(path)
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def get_prusa_backend_kwargs(config):
    """Extract PrusaGcodeBackend keyword arguments from config."""
    printer = config["printer"]
    limits = config["motion_limits"]

    return {
        "port": printer["port"],
        "baudrate": printer["baudrate"],
        "x_limits": tuple(limits["x"]),
        "y_limits": tuple(limits["y"]),
        "z_limits": tuple(limits["z"]),
    }


def get_safe_feedrates(config):
    """Extract safe feedrates from config."""
    return config["safe_feedrates"]


def get_scan_mode_presets(config):
    """Extract scan-mode hardware and timing presets."""
    return config.get("scan_mode_presets", {})


def get_scan_mode_preset(config, mode):
    """Return the preset for a scan mode, or fall back to the default scan area."""
    presets = get_scan_mode_presets(config)
    if mode in presets:
        return presets[mode]

    return {
        "description": "Default scan profile from project configuration.",
        "scan_area": config["scan_area"],
        "feedrates": get_safe_feedrates(config),
        "z_control": {
            "feedback": "default Z dry-run profile",
            "approach_start": config["scan_area"]["z"],
            "approach_target": config["scan_area"]["z"],
            "retract_target": config["scan_area"]["z"],
            "step_size": 1,
            "dwell_ms": 50,
            "auto_approach_ready": False,
            "manual_move_ready": True,
        },
        "hardware": {
            "xy_stage": "configured XY controller",
            "z_stage": "configured Z controller",
            "sensor": "configured acquisition channel",
        },
    }


def get_safe_raster_config(config):
    """Extract safe educational raster settings from config."""
    return config["safe_raster"]


def get_parking_position(config):
    """Extract the safe workstation parking position."""
    return config["parking_position"]
