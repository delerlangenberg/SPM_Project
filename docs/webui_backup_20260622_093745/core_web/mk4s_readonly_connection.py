from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any
import time

from core.web.hardware_dev_logger import HardwareDevLogger, redact


READONLY_COMMANDS = ["M115", "M105", "M119", "M114"]

PRUSA_USB_VID = "VID:PID=2C99:"
PRUSA_USB_PID_ALLOWLIST = {"000D", "001A"}

FORBIDDEN_PREFIXES = (
    "G0", "G00", "G1", "G01",
    "G28", "G29",
    "M17", "M18", "M80", "M81",
    "M104", "M109", "M140", "M190",
    "M302", "M500", "M501", "M502",
)


@dataclass
class RealHardwareConnectionResult:
    ok: bool
    ready: bool
    mode: str
    port: str
    baud: int
    message: str
    firmware: str
    machine_type: str
    temperature: str
    endstops: str
    position: str
    safety: str
    log_lines: list[str]
    transcript: list[str]
    dev_log_path_txt: str
    dev_log_path_jsonl: str


def validate_readonly_commands() -> None:
    for command in READONLY_COMMANDS:
        normalized = command.strip().upper()
        for forbidden in FORBIDDEN_PREFIXES:
            if normalized.startswith(forbidden):
                raise RuntimeError(f"Unsafe command blocked: {command}")


def list_serial_ports() -> list[dict[str, str]]:
    try:
        from serial.tools import list_ports
    except Exception as exc:
        return [{"device": "", "description": "", "hwid": "", "error": str(exc)}]

    ports: list[dict[str, str]] = []
    for p in list_ports.comports():
        ports.append(
            {
                "device": str(p.device or ""),
                "description": str(p.description or ""),
                "hwid": str(p.hwid or ""),
            }
        )
    return ports


def choose_prusa_port(logger: HardwareDevLogger | None = None) -> str:
    ports = list_serial_ports()

    if logger:
        logger.emit("INFO", "port_scan_start", count=len(ports))

    for p in ports:
        if logger:
            logger.emit(
                "INFO",
                "port_seen",
                device=p.get("device", ""),
                description=p.get("description", ""),
                hwid=p.get("hwid", ""),
            )

    for p in ports:
        hwid = p.get("hwid", "")
        matched_pid = next((pid for pid in PRUSA_USB_PID_ALLOWLIST if f"{PRUSA_USB_VID}{pid}" in hwid), "")
        if matched_pid:
            if logger:
                logger.emit(
                    "PASS",
                    "port_selected",
                    reason="matched_prusa_usb_vid_pid",
                    usb_pid=matched_pid,
                    device=p.get("device", ""),
                    description=p.get("description", ""),
                    hwid=p.get("hwid", ""),
                )
            return p.get("device", "")

    for p in ports:
        device = p.get("device", "")
        description = p.get("description", "").lower()
        hwid = p.get("hwid", "").lower()

        looks_usb = "usb" in description or "usb" in hwid
        looks_bad = "active management" in description or "pnp0501" in hwid

        if device and looks_usb and not looks_bad:
            if logger:
                logger.emit(
                    "WARN",
                    "port_selected",
                    reason="fallback_usb_serial_device",
                    device=p.get("device", ""),
                    description=p.get("description", ""),
                    hwid=p.get("hwid", ""),
                )
            return device

    if logger:
        logger.emit("FAIL", "port_selected", reason="no_prusa_usb_port_found")

    return ""


def _read_available(ser: Any, seconds: float, logger: HardwareDevLogger) -> list[str]:
    lines: list[str] = []
    deadline = time.time() + seconds

    logger.emit("INFO", "startup_buffer_read_start", seconds=seconds)

    while time.time() < deadline:
        raw = ser.readline()
        if not raw:
            continue

        text = raw.decode("utf-8", errors="replace").rstrip()
        if text:
            lines.append(text)
            logger.emit_raw("printer_startup_line", text)

    logger.emit("INFO", "startup_buffer_read_done", lines=len(lines))
    return lines


def _send_readonly_command(
    ser: Any,
    command: str,
    timeout_seconds: float,
    logger: HardwareDevLogger,
) -> list[str]:
    validate_readonly_commands()

    command = command.strip().upper()
    if command not in READONLY_COMMANDS:
        logger.emit("FAIL", "command_blocked", command=command, reason="not_in_readonly_allowlist")
        raise RuntimeError(f"Command not allowed in read-only hardware mode: {command}")

    logger.emit(
        "SAFE",
        "command_allowed",
        command=command,
        policy="read_only_allowlist",
        forbidden="movement_homing_heating_writes",
    )

    ser.write((command + "\n").encode("ascii"))
    ser.flush()

    logger.emit_raw("command_sent", command, command=command)

    lines = [f">>> {command}"]
    deadline = time.time() + timeout_seconds
    got_ok = False

    while time.time() < deadline:
        raw = ser.readline()
        if not raw:
            continue

        text = raw.decode("utf-8", errors="replace").rstrip()
        if not text:
            continue

        lines.append(text)
        logger.emit_raw("printer_response", text, command=command)

        if text.strip().lower() == "ok" or text.strip().lower().startswith("ok "):
            got_ok = True
            break

    logger.emit(
        "PASS" if got_ok else "WARN",
        "command_complete",
        command=command,
        ok=got_ok,
        response_lines=max(0, len(lines) - 1),
    )

    return lines


def _extract_command_block(command: str, transcript: list[str]) -> list[str]:
    marker = f"=== COMMAND {command} ==="
    result: list[str] = []
    inside = False

    for line in transcript:
        if line == marker:
            inside = True
            continue

        if inside and line.startswith("=== COMMAND "):
            break

        if inside:
            result.append(line)

    return result


def _summarize(transcript: list[str]) -> tuple[str, str, str, str, str]:
    m115 = _extract_command_block("M115", transcript)
    m105 = _extract_command_block("M105", transcript)
    m119 = _extract_command_block("M119", transcript)
    m114 = _extract_command_block("M114", transcript)

    firmware = ""
    machine = ""

    for line in m115:
        if "FIRMWARE_NAME:" in line:
            firmware = redact(line)
            if "MACHINE_TYPE:" in line:
                machine = line.split("MACHINE_TYPE:", 1)[1].split()[0].strip()

    temperature = ""
    for line in m105:
        if line.startswith("ok ") or " T:" in line:
            temperature = redact(line)

    endstops = "; ".join(
        redact(line) for line in m119
        if ":" in line and ("_min:" in line or "_max:" in line)
    )

    position = ""
    for line in m114:
        if line.startswith("X:") and "Y:" in line and "Z:" in line:
            position = redact(line)

    return firmware, machine, temperature, endstops, position


def connect_real_hardware_readonly(
    port: str | None = None,
    baud: int = 115200,
    timeout_seconds: float = 5.0,
    settle_seconds: float = 0.35,
) -> dict[str, Any]:
    logger = HardwareDevLogger("phase_2_2c_on_connect_readonly")

    logger.emit(
        "INFO",
        "phase_goal",
        goal="system_on_auto_detect_connect_exchange_readonly_ready_to_start",
    )
    logger.emit(
        "SAFE",
        "safety_policy",
        allowed=", ".join(READONLY_COMMANDS),
        blocked=", ".join(FORBIDDEN_PREFIXES),
        meaning="no_movement_no_homing_no_heating_no_printer_writes",
    )

    try:
        validate_readonly_commands()
        logger.emit("PASS", "readonly_allowlist_validation", commands=", ".join(READONLY_COMMANDS))
    except Exception as exc:
        logger.emit("FAIL", "readonly_allowlist_validation", error=str(exc))
        return asdict(
            RealHardwareConnectionResult(
                ok=False,
                ready=False,
                mode="real_hardware_readonly",
                port="",
                baud=baud,
                message=f"Safety validation failed: {exc}",
                firmware="",
                machine_type="",
                temperature="",
                endstops="",
                position="",
                safety="blocked_before_serial_open",
                log_lines=logger.summary_lines(),
                transcript=[],
                dev_log_path_txt=str(logger.text_path),
                dev_log_path_jsonl=str(logger.jsonl_path),
            )
        )

    selected_port = port or choose_prusa_port(logger)
    if not selected_port:
        logger.emit("FAIL", "connect_aborted", reason="no_prusa_mk4s_usb_serial_port_found")
        return asdict(
            RealHardwareConnectionResult(
                ok=False,
                ready=False,
                mode="real_hardware_readonly",
                port="",
                baud=baud,
                message="No Prusa MK4S USB serial port found.",
                firmware="",
                machine_type="",
                temperature="",
                endstops="",
                position="",
                safety="no_serial_port_selected",
                log_lines=logger.summary_lines(),
                transcript=[],
                dev_log_path_txt=str(logger.text_path),
                dev_log_path_jsonl=str(logger.jsonl_path),
            )
        )

    try:
        import serial
    except Exception as exc:
        logger.emit("FAIL", "serial_import_failed", error=str(exc))
        return asdict(
            RealHardwareConnectionResult(
                ok=False,
                ready=False,
                mode="real_hardware_readonly",
                port=selected_port,
                baud=baud,
                message=f"pyserial is not available: {exc}",
                firmware="",
                machine_type="",
                temperature="",
                endstops="",
                position="",
                safety="serial_library_missing",
                log_lines=logger.summary_lines(),
                transcript=[],
                dev_log_path_txt=str(logger.text_path),
                dev_log_path_jsonl=str(logger.jsonl_path),
            )
        )

    transcript: list[str] = []
    transcript.append("PHASE 2.2C SYSTEM ON REAL HARDWARE READ-ONLY CONNECTION")
    transcript.append(f"port={selected_port}")
    transcript.append(f"baud={baud}")
    transcript.append("allowed_commands=" + ", ".join(READONLY_COMMANDS))
    transcript.append("safety=no movement, no homing, no heating")
    transcript.append("")

    try:
        logger.emit("INFO", "serial_open_attempt", port=selected_port, baud=baud)
        with serial.Serial(
            port=selected_port,
            baudrate=baud,
            timeout=0.25,
            write_timeout=2,
        ) as ser:
            logger.emit("PASS", "serial_open_ok", port=selected_port, baud=baud)
            logger.emit("INFO", "serial_settle_wait", seconds=settle_seconds)
            time.sleep(settle_seconds)

            startup_lines = _read_available(ser, 0.30, logger)
            if startup_lines:
                transcript.append("=== STARTUP / BUFFERED LINES ===")
                transcript.extend(startup_lines)
                transcript.append("")

            for command in READONLY_COMMANDS:
                transcript.append(f"=== COMMAND {command} ===")
                transcript.extend(_send_readonly_command(ser, command, timeout_seconds, logger))
                transcript.append("")

        logger.emit("PASS", "serial_closed_cleanly", port=selected_port)

    except Exception as exc:
        transcript.append(f"ERROR: {exc}")
        logger.emit("FAIL", "hardware_connection_failed", port=selected_port, error=str(exc))
        return asdict(
            RealHardwareConnectionResult(
                ok=False,
                ready=False,
                mode="real_hardware_readonly",
                port=selected_port,
                baud=baud,
                message=f"Real hardware connection failed: {exc}",
                firmware="",
                machine_type="",
                temperature="",
                endstops="",
                position="",
                safety="failed_during_readonly_handshake",
                log_lines=logger.summary_lines(),
                transcript=transcript,
                dev_log_path_txt=str(logger.text_path),
                dev_log_path_jsonl=str(logger.jsonl_path),
            )
        )

    firmware, machine, temperature, endstops, position = _summarize(transcript)

    logger.emit(
        "INFO",
        "parsed_hardware_identity",
        firmware=firmware or "not_found",
        machine_type=machine or "not_found",
    )
    logger.emit("INFO", "parsed_temperature", temperature=temperature or "not_found")
    logger.emit("INFO", "parsed_endstops", endstops=endstops or "not_found")
    logger.emit("INFO", "parsed_position", position=position or "not_found")

    ready = bool(firmware and temperature and endstops and position)
    message = (
        "Real hardware connected. MK4S read-only handshake OK. Ready to start."
        if ready
        else "Real hardware connected, but read-only handshake is incomplete. Not ready."
    )

    logger.emit(
        "PASS" if ready else "FAIL",
        "ready_state",
        ready=ready,
        message=message,
        port=selected_port,
        machine_type=machine or "not_found",
    )
    logger.emit(
        "INFO",
        "share_this_log",
        text_log=str(logger.text_path),
        jsonl_log=str(logger.jsonl_path),
    )

    return asdict(
        RealHardwareConnectionResult(
            ok=ready,
            ready=ready,
            mode="real_hardware_readonly",
            port=selected_port,
            baud=baud,
            message=message,
            firmware=firmware,
            machine_type=machine,
            temperature=temperature,
            endstops=endstops,
            position=position,
            safety="no_movement_no_homing_no_heating_no_writes",
            log_lines=logger.summary_lines(),
            transcript=transcript,
            dev_log_path_txt=str(logger.text_path),
            dev_log_path_jsonl=str(logger.jsonl_path),
        )
    )


if __name__ == "__main__":
    import json
    print(json.dumps(connect_real_hardware_readonly(), indent=2, ensure_ascii=False))
