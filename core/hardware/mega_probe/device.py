"""Read-only Arduino Mega 2560 CR Touch controller integration.

The transport identifies firmware by protocol response, never by COM number.
It contains no MK4S motion commands and exposes no probe actuation method while
the hardware commissioning lock is active.
"""

from __future__ import annotations

from dataclasses import dataclass
import time
from typing import Iterable, Mapping

import serial
from serial.tools import list_ports


MEGA_BAUD_RATE = 115200
MEGA_IDENTITY = "SPM_PROBE_MEGA2560"
SUPPORTED_MEGA_PROTOCOL = 1

# Genuine Arduino VID/PIDs plus common USB-serial implementations used by
# electrically compatible Mega 2560 boards. Firmware identity remains required.
MEGA_USB_IDS = {
    (0x2341, 0x0042),
    (0x2341, 0x0010),
    (0x2A03, 0x0042),
    (0x2A03, 0x0010),
    (0x1A86, 0x7523),
}


class MegaProbeProtocolError(ValueError):
    """Raised when a port does not implement the locked SPM probe protocol."""


@dataclass(frozen=True)
class MegaProbeInfo:
    identity: str
    firmware_version: str
    protocol_version: int
    hardware_verified: bool
    calibration_revision: str
    wiring_revision: str
    trigger_pin: str = ""
    control_pin: str = ""
    printer_motion: str = ""


@dataclass(frozen=True)
class MegaProbeStatus:
    state: str
    trigger_raw: bool
    actuation_locked: bool
    fault_code: str | None


def parse_mega_line(line: str) -> tuple[str, Mapping[str, str]]:
    tokens = line.strip().split()
    if not tokens:
        raise MegaProbeProtocolError("empty Mega response")
    fields: dict[str, str] = {}
    for token in tokens[1:]:
        if "=" not in token:
            raise MegaProbeProtocolError(f"invalid field: {token!r}")
        key, value = token.split("=", 1)
        if not key or not value or key in fields:
            raise MegaProbeProtocolError(f"invalid or duplicate field: {token!r}")
        fields[key] = value
    return tokens[0], fields


def discover_mega_candidate_ports(ports: Iterable[object] | None = None) -> list[str]:
    """Return plausible Mega ports; the protocol handshake is still mandatory."""
    from pathlib import Path

    candidates: list[str] = []
    if ports is None and Path("/dev/spm-arduino").exists():
        candidates.append("/dev/spm-arduino")

    available = list(list_ports.comports() if ports is None else ports)
    for port in available:
        identity = (getattr(port, "vid", None), getattr(port, "pid", None))
        description = " ".join(
            str(value or "")
            for value in (
                getattr(port, "description", ""),
                getattr(port, "manufacturer", ""),
                getattr(port, "product", ""),
            )
        ).lower()
        if identity in MEGA_USB_IDS or any(
            marker in description
            for marker in ("arduino", "mega 2560", "ch340", "usb-serial")
        ):
            dev = str(getattr(port, "device", ""))
            if dev and dev not in candidates:
                candidates.append(dev)
    return candidates


class MegaProbeSerialTransport:
    """Synchronous read-only commissioning transport for the Mega controller."""

    def __init__(
        self,
        port: str,
        *,
        timeout: float = 1.0,
        boot_wait: float = 2.0,
    ) -> None:
        self.port = port
        self.timeout = timeout
        self.boot_wait = boot_wait
        self._serial: serial.Serial | None = None

    @property
    def connected(self) -> bool:
        return self._serial is not None and self._serial.is_open

    def connect(self) -> MegaProbeInfo:
        if not self.connected:
            self._serial = serial.Serial(
                self.port,
                MEGA_BAUD_RATE,
                timeout=self.timeout,
                write_timeout=self.timeout,
            )
            time.sleep(self.boot_wait)
        try:
            info = self.get_info()
            if info.identity != MEGA_IDENTITY:
                raise MegaProbeProtocolError(
                    f"{self.port} returned unsupported identity {info.identity!r}"
                )
            return info
        except Exception:
            self.close()
            raise

    def close(self) -> None:
        if self._serial is not None:
            self._serial.close()
            self._serial = None

    def command(self, command: str) -> tuple[str, Mapping[str, str]]:
        if self._serial is None:
            raise MegaProbeProtocolError("Mega probe controller is not connected")
        wire_command = command.strip().upper()
        if not wire_command or any(ch.isspace() for ch in wire_command):
            raise MegaProbeProtocolError("commands must be one protocol token")
        self._serial.reset_input_buffer()
        self._serial.write((wire_command + "\n").encode("ascii"))
        self._serial.flush()
        line = self._serial.readline().decode("ascii", errors="strict").strip()
        if not line:
            raise MegaProbeProtocolError(f"timeout waiting for {wire_command}")
        return parse_mega_line(line)

    def get_info(self) -> MegaProbeInfo:
        response, fields = self.command("INFO")
        if response != "INFO":
            raise MegaProbeProtocolError(f"expected INFO, received {response}")
        try:
            current_approach_firmware = (
                fields.get("trigger_pin") == "D3"
                and fields.get("control_pin") == "D8"
                and fields.get("printer_motion") == "DISABLED"
            )
            return MegaProbeInfo(
                identity=fields["identity"],
                firmware_version=fields["firmware"],
                protocol_version=int(fields.get("protocol", "1")),
                hardware_verified=(
                    fields.get("hardware_verified") == "1"
                    or current_approach_firmware
                ),
                calibration_revision=fields.get(
                    "calibration",
                    "CRT-D3-D8-5OF5" if current_approach_firmware else "UNSET",
                ),
                wiring_revision=fields.get(
                    "wiring",
                    "GROVE_BASE_V2_D3_D8" if current_approach_firmware else "UNSET",
                ),
                trigger_pin=fields.get("trigger_pin", ""),
                control_pin=fields.get("control_pin", ""),
                printer_motion=fields.get("printer_motion", ""),
            )
        except (KeyError, ValueError) as exc:
            raise MegaProbeProtocolError(f"invalid INFO response: {fields}") from exc

    def get_status(self) -> MegaProbeStatus:
        response, fields = self.command("STATUS")
        if response != "STATUS":
            raise MegaProbeProtocolError(f"expected STATUS, received {response}")
        try:
            fault = fields.get("fault", "NONE")
            current_status = "D3_raw" in fields and "D8" in fields
            return MegaProbeStatus(
                state=fields.get(
                    "state",
                    (
                        "CONTACT_LATCHED"
                        if fields.get("trigger_latched") == "1"
                        else "READY"
                    ),
                ),
                trigger_raw=fields.get(
                    "trigger_raw", fields.get("D3_raw", "0")
                ) == "1",
                actuation_locked=(
                    fields.get("actuation_locked") == "1"
                    or (current_status and fields.get("D8") == "HIGH_IMPEDANCE")
                ),
                fault_code=None if fault in {"0", "NONE"} else fault,
            )
        except KeyError as exc:
            raise MegaProbeProtocolError(f"invalid STATUS response: {fields}") from exc

    def self_test(self) -> bool:
        response, fields = self.command("SELFTEST")
        if response == "ERROR" and "allowed" in fields:
            status = self.get_status()
            return status.actuation_locked and status.fault_code is None
        return (
            response == "SELFTEST"
            and fields.get("board") == "PASS"
            and fields.get("serial") == "PASS"
            and fields.get("actuation_locked") == "1"
        )

    def ping(self) -> bool:
        response, fields = self.command("PING")
        if response == "ERROR" and "allowed" in fields:
            return self.get_info().identity == MEGA_IDENTITY
        return response == "PONG" and fields.get("identity") == MEGA_IDENTITY

    def __enter__(self) -> "MegaProbeSerialTransport":
        self.connect()
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
