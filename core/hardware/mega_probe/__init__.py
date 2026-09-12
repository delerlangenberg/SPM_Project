"""Arduino Mega 2560 CR Touch controller boundary."""

from .device import (
    MEGA_BAUD_RATE,
    MEGA_IDENTITY,
    MEGA_USB_IDS,
    SUPPORTED_MEGA_PROTOCOL,
    MegaProbeInfo,
    MegaProbeProtocolError,
    MegaProbeSerialTransport,
    MegaProbeStatus,
    discover_mega_candidate_ports,
    parse_mega_line,
)

__all__ = [
    "MEGA_BAUD_RATE",
    "MEGA_IDENTITY",
    "MEGA_USB_IDS",
    "SUPPORTED_MEGA_PROTOCOL",
    "MegaProbeInfo",
    "MegaProbeProtocolError",
    "MegaProbeSerialTransport",
    "MegaProbeStatus",
    "discover_mega_candidate_ports",
    "parse_mega_line",
]
