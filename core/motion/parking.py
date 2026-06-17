from __future__ import annotations

from core.education.config_loader import get_parking_position, get_prusa_backend_kwargs
from core.motion.prusa_gcode_backend import PrusaGcodeBackend


def park_mk4s(config: dict) -> dict:
    """Park MK4S by retracting Z first, then moving XY to the parking corner."""
    parking = get_parking_position(config)
    feedrates = config["safe_feedrates"]
    backend = PrusaGcodeBackend(**get_prusa_backend_kwargs(config))

    try:
        backend.connect()
        backend.move_to(z=float(parking["z"]), feedrate=feedrates["z"])
        backend.move_to(
            x=float(parking["x"]),
            y=float(parking["y"]),
            feedrate=feedrates["xy"],
        )
        return backend.get_state()
    finally:
        backend.disconnect()
