from __future__ import annotations

from dataclasses import dataclass, field

from core.motion.prusa_gcode_backend import PrusaGcodeBackend


@dataclass(frozen=True)
class HardwareCheck:
    name: str
    status: str
    message: str
    details: tuple[str, ...] = field(default_factory=tuple)

    @property
    def ok(self) -> bool:
        return self.status == "PASS"


@dataclass(frozen=True)
class HardwareDiagnosticReport:
    checks: tuple[HardwareCheck, ...]

    @property
    def passed(self) -> bool:
        blocking_statuses = {"FAIL"}
        return not any(check.status in blocking_statuses for check in self.checks)

    def summary_lines(self) -> list[str]:
        lines = ["Hardware communication report:"]
        for check in self.checks:
            lines.append(f"- {check.status}: {check.name} - {check.message}")
            lines.extend(f"  {detail}" for detail in check.details)
        lines.append(f"Overall: {'PASS' if self.passed else 'FAIL'}")
        return lines

    def summary_text(self) -> str:
        return "\n".join(self.summary_lines())


def list_serial_ports() -> list[str]:
    try:
        from serial.tools import list_ports  # type: ignore
    except Exception:
        return []

    return [
        f"{port.device}: {port.description}"
        for port in list_ports.comports()
    ]


def check_serial_inventory(ignored_ports: tuple[str, ...] = ("COM4",)) -> HardwareCheck:
    ports = list_serial_ports()
    if not ports:
        return HardwareCheck(
            name="Serial ports",
            status="WARN",
            message="No serial ports detected by pyserial.",
        )

    ignored = [
        port for port in ports
        if any(port.upper().startswith(ignored_port.upper()) for ignored_port in ignored_ports)
    ]
    active = [port for port in ports if port not in ignored]
    details = tuple([f"Detected: {port}" for port in active] + [f"Ignored phantom: {port}" for port in ignored])

    return HardwareCheck(
        name="Serial ports",
        status="PASS" if active else "WARN",
        message=f"{len(active)} active serial candidate(s), {len(ignored)} ignored.",
        details=details,
    )


def check_prusa_communication(config: dict) -> HardwareCheck:
    printer = config["printer"]
    port = str(printer["port"])
    baudrate = int(printer["baudrate"])
    backend = PrusaGcodeBackend(
        port=port,
        baudrate=baudrate,
        timeout=0.5,
        auto_detect_port=False,
    )

    try:
        backend.connect()
        firmware_lines = backend.send_gcode("M115", timeout=4.0)
        position_lines = backend.send_gcode("M114", timeout=4.0)
        state = backend.get_state()
    except Exception as error:
        return HardwareCheck(
            name="Prusa MK4S XY motion controller",
            status="FAIL",
            message=f"Communication failed on {port}: {error}",
        )
    finally:
        backend.disconnect()

    details = (
        f"Port: {port}",
        f"Baudrate: {baudrate}",
        f"M115: {' | '.join(firmware_lines) if firmware_lines else 'no response text'}",
        f"M114: {' | '.join(position_lines) if position_lines else 'no response text'}",
        f"State: {state}",
    )
    return HardwareCheck(
        name="Prusa MK4S XY motion controller",
        status="PASS",
        message="No-motion firmware and position queries completed.",
        details=details,
    )


def check_z_controller_status() -> HardwareCheck:
    return HardwareCheck(
        name="Future fine Z scanner",
        status="WARN",
        message="Fine Z scanner communication is not part of the current MK4S-original hardware test.",
        details=(
            "Current hardware test uses the original Prusa MK4S X/Y/Z motion system.",
            "Approach/feedback controls are dry-run training until the later Z subsystem is mounted and assigned a confirmed port.",
        ),
    )


def check_motion_envelope(config: dict) -> HardwareCheck:
    limits = config["motion_limits"]
    safe_limits = config.get("spm_safe_limits", limits)
    scan_area = config["scan_area"]
    details = (
        f"Machine limits: X {limits['x']}, Y {limits['y']}, Z {limits['z']}",
        f"Recommended SPM-safe limits: X {safe_limits['x']}, Y {safe_limits['y']}, Z {safe_limits['z']}",
        (
            "Configured scan: "
            f"X {scan_area['x_min']}..{scan_area['x_max']}, "
            f"Y {scan_area['y_min']}..{scan_area['y_max']}, "
            f"Z {scan_area['z']}, "
            f"{scan_area['x_resolution']} x {scan_area['y_resolution']}"
        ),
    )
    return HardwareCheck(
        name="Configured machine and SPM-safe envelopes",
        status="PASS",
        message="Original MK4S machine limits and recommended SPM-safe limits loaded from configuration.",
        details=details,
    )


def run_hardware_communication_report(config: dict) -> HardwareDiagnosticReport:
    checks = (
        check_serial_inventory(),
        check_motion_envelope(config),
        check_prusa_communication(config),
        check_z_controller_status(),
    )
    return HardwareDiagnosticReport(checks=checks)
