from __future__ import annotations

from dataclasses import dataclass


@dataclass
class WorkstationStatus:
    machine_port: str
    machine_baudrate: int
    motion_limits_summary: str
    system_check_passed: bool = False
    real_motion_enabled: bool = False
    scan_profile_valid: bool = False
    last_scan_mode: str = "IDLE"
    last_output_file: str = "not selected"
    last_plot_file: str = "not generated"
    z_connected: bool = False
    z_last_command: str = "initialized"
    acquisition_points: int = 0
    acquisition_status: str = "waiting for scan data"
    safety_message: str = "Safe mode active; real motion disabled"

    @classmethod
    def from_config(cls, config: dict) -> "WorkstationStatus":
        limits = config["motion_limits"]
        printer = config["printer"]
        return cls(
            machine_port=str(printer["port"]),
            machine_baudrate=int(printer["baudrate"]),
            motion_limits_summary=(
                f"X {limits['x'][0]}-{limits['x'][1]}, "
                f"Y {limits['y'][0]}-{limits['y'][1]}, "
                f"Z {limits['z'][0]}-{limits['z'][1]}"
            ),
            last_output_file=str(config["safe_raster"]["output_file"]),
        )

    def record_validation_pass(self) -> None:
        self.scan_profile_valid = True
        self.safety_message = "Profile valid; real motion still requires system check"

    def record_validation_fail(self, reason: str) -> None:
        self.scan_profile_valid = False
        self.real_motion_enabled = False
        self.safety_message = f"Validation failed: {reason}"

    def record_system_check_pass(self) -> None:
        self.system_check_passed = True
        self.safety_message = "System check passed; real motion can be enabled"

    def record_system_check_fail(self, reason: str) -> None:
        self.system_check_passed = False
        self.real_motion_enabled = False
        self.safety_message = f"System check failed: {reason}"

    def enable_real_motion(self) -> None:
        if not self.system_check_passed:
            raise RuntimeError("Run system check before enabling real motion")
        self.real_motion_enabled = True
        self.safety_message = "Real motion enabled; hardware commands allowed"

    def disable_real_motion(self) -> None:
        self.real_motion_enabled = False
        self.safety_message = "Real motion disabled; hardware commands blocked"

    def record_z_status(self, status: dict[str, object]) -> None:
        self.z_connected = bool(status["connected"])
        self.z_last_command = str(status["last_command"])

    def record_scan_start(self, mode: str, output_file: str) -> None:
        self.last_scan_mode = mode
        self.last_output_file = output_file
        self.acquisition_status = "scan running"

    def record_scan_output(self, output_file: str, plot_file: str, point_count: int) -> None:
        self.last_output_file = output_file
        self.last_plot_file = plot_file
        self.acquisition_points = point_count
        self.acquisition_status = f"{point_count} raster points loaded"

    def machine_summary(self) -> str:
        return (
            f"Machine: Prusa MK4S on {self.machine_port} @ {self.machine_baudrate}; "
            f"limits {self.motion_limits_summary}"
        )

    def workflow_summary(self) -> str:
        check = "PASS" if self.system_check_passed else "WAITING"
        motion = "ENABLED" if self.real_motion_enabled else "DISABLED"
        validation = "VALID" if self.scan_profile_valid else "NOT VALIDATED"
        return f"Workflow: validation {validation}; system check {check}; real motion {motion}"

    def safety_summary(self) -> str:
        return f"Safety State: {self.safety_message}"

    def output_summary(self) -> str:
        return f"Output: CSV {self.last_output_file}; PNG {self.last_plot_file}"

    def acquisition_summary(self) -> str:
        return f"Acquisition: {self.acquisition_status}"
