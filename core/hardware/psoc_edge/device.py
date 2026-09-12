"""Hardware-neutral contract for the PSoC E84 SPM Edge Controller.

This module deliberately contains no printer-motion commands. The approach
coordinator must combine this device with the existing, separately authorized
xBuddy motion driver.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable, Mapping

import serial
from serial.tools import list_ports


INFINEON_USB_VID = 0x04B4
KITPROG3_USB_UART_PID = 0xF155
PRUSA_USB_VID = 0x2C99
PRUSA_MK4S_USB_PID = 0x001A
EDGE_BAUD_RATE = 115200


class EdgeProtocolError(ValueError):
    """Raised when the edge-controller transport returns malformed data."""


class EdgeControllerState(str, Enum):
    DISCONNECTED = "DISCONNECTED"
    SAFE_OFF = "SAFE_OFF"
    READY_STOWED = "READY_STOWED"
    ARMED_DEPLOYED = "ARMED_DEPLOYED"
    TRIGGERED = "TRIGGERED"
    FAULT = "FAULT"


@dataclass(frozen=True)
class EdgeCapabilities:
    contact_probe: bool = True
    analog_probe: bool = False
    environmental_sensors: bool = True
    vibration_monitor: bool = True
    local_logging: bool = True
    wireless_diagnostics: bool = True
    embedded_ml: bool = True


@dataclass(frozen=True)
class EdgeControllerInfo:
    board_id: str
    firmware_version: str
    protocol_version: int
    serial_number: str
    hardware_verified: bool
    calibration_revision: str
    capabilities: EdgeCapabilities = EdgeCapabilities()


@dataclass(frozen=True)
class EdgeControllerStatus:
    state: EdgeControllerState
    hardware_verified: bool
    outputs_locked: bool
    fault_code: str | None


@dataclass(frozen=True)
class EdgeDiagnostics:
    board_ok: bool
    uart_ok: bool
    probe_power: str
    probe_input: str
    probe_control: str
    hardware_verified: bool


def parse_edge_line(line: str) -> tuple[str, Mapping[str, str]]:
    """Parse one commissioning-protocol line without accepting ambiguity."""

    tokens = line.strip().split()
    if not tokens:
        raise EdgeProtocolError("empty edge-controller response")
    fields: dict[str, str] = {}
    for token in tokens[1:]:
        if "=" not in token:
            raise EdgeProtocolError(f"invalid field: {token!r}")
        key, value = token.split("=", 1)
        if not key or not value or key in fields:
            raise EdgeProtocolError(f"invalid or duplicate field: {token!r}")
        fields[key] = value
    return tokens[0], fields


def discover_edge_ports(ports: Iterable[object] | None = None) -> list[str]:
    """Return the E84 KitProg3 USB-UART ports by exact USB VID/PID."""

    available = list(list_ports.comports() if ports is None else ports)
    return sorted(
        str(port.device)
        for port in available
        if getattr(port, "vid", None) == INFINEON_USB_VID
        and getattr(port, "pid", None) == KITPROG3_USB_UART_PID
    )


class EdgeSerialTransport:
    """Synchronous commissioning transport for the KitProg3 USB-UART."""

    def __init__(self, port: str, *, timeout: float = 1.0) -> None:
        self.port = port
        self.timeout = timeout
        self._serial: serial.Serial | None = None

    @property
    def connected(self) -> bool:
        return self._serial is not None and self._serial.is_open

    def connect(self) -> EdgeControllerInfo:
        if self.connected:
            return self.get_info()
        self._serial = serial.Serial(
            self.port,
            EDGE_BAUD_RATE,
            timeout=self.timeout,
            write_timeout=self.timeout,
        )
        try:
            response, fields = self.command("HELLO")
            if response != "READY" or fields.get("board") != "KIT_PSE84_AI":
                raise EdgeProtocolError(
                    f"{self.port} is not an SPM Edge controller: {response} {fields}"
                )
            return self.get_info()
        except Exception:
            self.close()
            raise

    def close(self) -> None:
        if self._serial is not None:
            self._serial.close()
            self._serial = None

    def command(self, command: str) -> tuple[str, Mapping[str, str]]:
        if self._serial is None:
            raise EdgeProtocolError("edge controller is not connected")
        wire_command = command.strip().upper()
        if not wire_command or any(ch.isspace() for ch in wire_command):
            raise EdgeProtocolError("commands must be one protocol token")
        self._serial.reset_input_buffer()
        self._serial.write((wire_command + "\n").encode("ascii"))
        self._serial.flush()
        line = self._serial.readline().decode("ascii", errors="strict").strip()
        if not line:
            raise EdgeProtocolError(f"timeout waiting for {wire_command}")
        if line.startswith("You opted to boot application:"):
            raise EdgeProtocolError(
                "KIT_PSE84_AI factory OOB menu is running; flash the locked "
                "SPM Edge firmware before attempting the protocol handshake"
            )
        return parse_edge_line(line)

    def get_info(self) -> EdgeControllerInfo:
        response, fields = self.command("GET_INFO")
        if response != "INFO":
            raise EdgeProtocolError(f"expected INFO, received {response}")
        try:
            return EdgeControllerInfo(
                board_id=fields["board"],
                firmware_version=fields["firmware"],
                protocol_version=int(fields["protocol"]),
                serial_number=fields["serial"],
                hardware_verified=fields["hardware_verified"] == "1",
                calibration_revision=fields["calibration"],
            )
        except (KeyError, ValueError) as exc:
            raise EdgeProtocolError(f"invalid INFO response: {fields}") from exc

    def get_status(self) -> EdgeControllerStatus:
        response, fields = self.command("GET_STATUS")
        if response != "STATUS":
            raise EdgeProtocolError(f"expected STATUS, received {response}")
        try:
            fault = fields.get("fault", "0")
            return EdgeControllerStatus(
                state=EdgeControllerState(fields["state"]),
                hardware_verified=fields["hardware_verified"] == "1",
                outputs_locked=fields["outputs"] == "LOCKED",
                fault_code=None if fault in {"0", "NONE"} else fault,
            )
        except (KeyError, ValueError) as exc:
            raise EdgeProtocolError(f"invalid STATUS response: {fields}") from exc

    def get_diagnostics(self) -> EdgeDiagnostics:
        response, fields = self.command("GET_DIAGNOSTICS")
        if response != "DIAGNOSTICS":
            raise EdgeProtocolError(f"expected DIAGNOSTICS, received {response}")
        try:
            return EdgeDiagnostics(
                board_ok=fields["board"] == "PASS",
                uart_ok=fields["uart"] == "PASS",
                probe_power=fields["probe_power"],
                probe_input=fields["probe_input"],
                probe_control=fields["probe_control"],
                hardware_verified=fields["hardware_verified"] == "1",
            )
        except KeyError as exc:
            raise EdgeProtocolError(f"invalid DIAGNOSTICS response: {fields}") from exc

    def ping(self) -> bool:
        response, fields = self.command("PING")
        return response == "PONG" and fields.get("board") == "KIT_PSE84_AI"

    def __enter__(self) -> "EdgeSerialTransport":
        self.connect()
        return self

    def __exit__(self, *_: object) -> None:
        self.close()


class EdgeControllerSimulator:
    """Deterministic simulator implementing the production safety states."""

    def __init__(self, *, hardware_verified: bool = False) -> None:
        self.hardware_verified = hardware_verified
        self.state = EdgeControllerState.SAFE_OFF
        self.trigger_count = 0
        self.last_trigger_us: int | None = None
        self.fault_code: str | None = None

    def self_test(self) -> bool:
        if not self.hardware_verified:
            self.state = EdgeControllerState.FAULT
            self.fault_code = "COMMISSIONING_LOCK"
            return False
        self.state = EdgeControllerState.READY_STOWED
        self.fault_code = None
        return True

    def deploy_and_arm(self) -> None:
        if self.state != EdgeControllerState.READY_STOWED:
            raise EdgeProtocolError(f"cannot deploy from {self.state.value}")
        self.state = EdgeControllerState.ARMED_DEPLOYED

    def inject_trigger(self, timestamp_us: int) -> None:
        if self.state != EdgeControllerState.ARMED_DEPLOYED:
            self.state = EdgeControllerState.FAULT
            self.fault_code = "UNEXPECTED_TRIGGER"
            raise EdgeProtocolError("trigger received while probe was not armed")
        if timestamp_us < 0:
            raise EdgeProtocolError("timestamp must be non-negative")
        self.trigger_count += 1
        self.last_trigger_us = timestamp_us
        self.state = EdgeControllerState.TRIGGERED

    def stow(self) -> None:
        if self.state not in {
            EdgeControllerState.ARMED_DEPLOYED,
            EdgeControllerState.TRIGGERED,
        }:
            raise EdgeProtocolError(f"cannot stow from {self.state.value}")
        self.state = EdgeControllerState.READY_STOWED

    def disarm(self) -> None:
        self.state = EdgeControllerState.SAFE_OFF
