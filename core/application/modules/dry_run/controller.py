"""Real-hardware dry run following an analytic virtual sample profile.

Unlike simulation, this module always routes XYZ commands to an explicitly
authorized hardware backend and records only hardware readback. It never falls
back to synthetic feedback.
"""

from __future__ import annotations

import os
import re
import time
from typing import Any, Callable, Protocol

from serial import Serial

from core.application.modules.simulation.sample_generator import SampleGenerator
from core.system.hardware_initialized_profile import get_motion_controller_settings, load_hardware_initialized_profile
from core.web.real_scan_control import validate_real_scan_profile
from core.web.spm_scan_simulation import WebScanProfile, raster_line_coordinates


class DryRunHardware(Protocol):
    def connect(self) -> None: ...
    def close(self) -> None: ...
    def move_absolute(self, x: float, y: float, z: float, feedrate: float) -> None: ...
    def read_position(self) -> dict[str, float]: ...
    def read_crtouch(self) -> dict[str, Any]: ...
    def retract(self, z: float, feedrate: float) -> None: ...
    def home_xy(self) -> None: ...


def hardware_dry_run_allowed() -> bool:
    return os.getenv("SPM_ALLOW_HARDWARE_DRY_RUN", "").strip().lower() in {"1", "true", "yes"}


class DryRunSerialBackend:
    """xBuddy motion transport; probe feedback requires the separate E84."""

    def __init__(self, port: str | None = None) -> None:
        settings = get_motion_controller_settings()
        self.port = port or str(settings["port"])
        self.baudrate = int(settings["baudrate"])
        self.serial: Serial | None = None

    def connect(self) -> None:
        self.serial = Serial(self.port, self.baudrate, timeout=0.25, write_timeout=1.0)
        time.sleep(0.4)
        self.serial.reset_input_buffer()
        self._command("M114")
        self._command("M119")
        self._command("G90")

    def close(self) -> None:
        if self.serial is not None:
            self.serial.close()
            self.serial = None

    def _command(self, command: str, timeout: float = 30.0) -> list[str]:
        if self.serial is None:
            raise RuntimeError("Dry-run hardware is not connected")
        self.serial.write((command + "\n").encode("ascii"))
        self.serial.flush()
        lines: list[str] = []
        deadline = time.time() + timeout
        while time.time() < deadline:
            raw = self.serial.readline()
            if not raw:
                continue
            line = raw.decode("utf-8", errors="replace").strip()
            if not line:
                continue
            lines.append(line)
            if line.lower().startswith("echo:busy"):
                deadline = time.time() + timeout
            elif line == "ok" or line.startswith("ok "):
                return lines
        raise TimeoutError(f"Hardware timeout after {command!r}: {lines[-3:]}")

    def move_absolute(self, x: float, y: float, z: float, feedrate: float) -> None:
        self._command(f"G1 X{x:.4f} Y{y:.4f} Z{z:.4f} F{feedrate:.0f}", timeout=90.0)
        self._command("M400", timeout=90.0)

    def read_position(self) -> dict[str, float]:
        text = "\n".join(self._command("M114"))
        values: dict[str, float] = {}
        for axis in ("X", "Y", "Z"):
            match = re.search(rf"\b{axis}:([+-]?\d+(?:\.\d+)?)", text)
            if match is None:
                raise RuntimeError(f"M114 did not contain {axis} position")
            values[axis.lower()] = float(match.group(1))
        return values

    def read_crtouch(self) -> dict[str, Any]:
        raise RuntimeError(
            "CR Touch feedback must come from the PSoC E84 USB protocol; "
            "xBuddy M119 is not CR Touch feedback"
        )

    def retract(self, z: float, feedrate: float) -> None:
        self._command(f"G1 Z{z:.4f} F{feedrate:.0f}", timeout=90.0)
        self._command("M400", timeout=90.0)

    def home_xy(self) -> None:
        self._command("G28 X Y", timeout=120.0)


def run_hardware_dry_run(
    profile: WebScanProfile,
    sample_type: str,
    sample_params: dict[str, float],
    *,
    scan_speed_mm_s: float,
    approach_speed_mm_s: float = 2.0,
    safe_retract_z_mm: float = 120.0,
    port: str | None = None,
    on_point: Callable[[dict[str, Any]], None] | None = None,
    backend: DryRunHardware | None = None,
) -> dict[str, Any]:
    """Move real XYZ hardware over the virtual profile and record hardware feedback."""
    validate_real_scan_profile(profile)
    if not hardware_dry_run_allowed() and backend is None:
        return {
            "ok": False,
            "status": "motion_locked",
            "message": "Hardware Dry Run is locked. Launch with SPM_ALLOW_HARDWARE_DRY_RUN=1.",
            "log_lines": ["DRY RUN BLOCKED: explicit hardware dry-run authorization is missing."],
        }
    if scan_speed_mm_s <= 0 or approach_speed_mm_s <= 0:
        raise ValueError("scan and approach speeds must be positive")

    device = backend or DryRunSerialBackend(port)
    sample = SampleGenerator(sample_type, sample_params)
    limits = load_hardware_initialized_profile()["hardware_initialized_profile"]["motion_limits"]
    z_min = float(limits["z_min"])
    z_max = float(limits["z_max"])
    targets = [
        profile.z_setpoint + sample.get_height_at_position(x, y)
        for line_index in range(profile.y_points)
        for x, y in raster_line_coordinates(profile, line_index)[0]
    ]
    if min(targets) < z_min or max(targets) > z_max:
        raise ValueError(f"virtual Z path {min(targets):.3f}..{max(targets):.3f} is outside hardware limits {z_min:.3f}..{z_max:.3f}")
    if not z_min <= safe_retract_z_mm <= z_max:
        raise ValueError("safe retract Z is outside hardware limits")
    xy_feedrate = max(30.0, min(float(scan_speed_mm_s), 50.0) * 60.0)
    z_feedrate = max(3.0, min(float(approach_speed_mm_s), 20.0) * 60.0)
    rows: list[list[dict[str, Any]]] = []
    log_lines = [
        f"HARDWARE DRY RUN: {profile.x_points} x {profile.y_points} points; sample={sample_type}.",
        f"HARDWARE DRY RUN: XY speed={scan_speed_mm_s:.3f} mm/s; approach speed={approach_speed_mm_s:.3f} mm/s.",
        "HARDWARE DRY RUN: XYZ movement is real; target Z comes from the virtual sample; position feedback is xBuddy M114 and probe feedback requires the PSoC E84 USB protocol.",
    ]
    connected = False
    try:
        device.connect()
        connected = True
        first_x, first_y = raster_line_coordinates(profile, 0)[0][0]
        initial_position = device.read_position()
        device.move_absolute(first_x, first_y, initial_position["z"], xy_feedrate)
        device.move_absolute(first_x, first_y, targets[0], z_feedrate)
        log_lines.append(
            f"HARDWARE DRY RUN: approach complete at X{first_x:.3f} Y{first_y:.3f} Z{targets[0]:.3f}."
        )
        for line_index in range(profile.y_points):
            coordinates, _direction = raster_line_coordinates(profile, line_index)
            row: list[dict[str, Any]] = []
            for point_index, (x, y) in enumerate(coordinates):
                virtual_height = sample.get_height_at_position(x, y)
                target_z = profile.z_setpoint + virtual_height
                device.move_absolute(x, y, target_z, xy_feedrate if point_index else z_feedrate)
                position = device.read_position()
                probe = device.read_crtouch()
                triggered = bool(probe["triggered"])
                point = {
                    "point_index": point_index,
                    "line_index": line_index,
                    "x": position["x"],
                    "y": position["y"],
                    "z_feedback": position["z"],
                    "measured_z": position["z"],
                    "commanded_z": target_z,
                    "surface_height": position["z"] - profile.z_setpoint,
                    "virtual_target_height": virtual_height,
                    "feedback_error": position["z"] - target_z,
                    "deflection": 1.0 if triggered else 0.0,
                    "amplitude": 1.0 if triggered else 0.0,
                    "crtouch_triggered": triggered,
                    "feedback_source": str(probe["source"]),
                }
                row.append(point)
                if on_point is not None:
                    on_point(dict(point))
            rows.append(row)
        return {
            "ok": True,
            "status": "complete",
            "message": "Hardware Dry Run complete using xBuddy M114 position and PSoC E84 CR Touch feedback.",
            "lines": rows,
            "log_lines": [*log_lines, "HARDWARE DRY RUN COMPLETE."],
        }
    except Exception as exc:
        return {
            "ok": False,
            "status": "hardware_failed",
            "message": f"Hardware Dry Run failed: {exc}",
            "lines": rows,
            "log_lines": [*log_lines, f"HARDWARE DRY RUN FAILED: {exc}"],
        }
    finally:
        if connected:
            try:
                device.retract(safe_retract_z_mm, z_feedrate)
                device.home_xy()
                log_lines.append(f"HARDWARE DRY RUN: retracted to Z{safe_retract_z_mm:.3f} and homed XY.")
            except Exception as cleanup_exc:
                log_lines.append(f"HARDWARE DRY RUN CLEANUP FAILED: {cleanup_exc}")
            finally:
                device.close()
