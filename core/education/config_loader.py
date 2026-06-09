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


def get_safe_raster_config(config):
    """Extract safe educational raster settings from config."""
    return config["safe_raster"]
