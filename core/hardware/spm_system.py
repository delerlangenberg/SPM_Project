"""Discovery and fail-closed readiness for the MK4S + Mega probe system.

This module performs no motion and opens no serial ports. USB identity finds
candidate devices; the caller must complete the Mega firmware handshake before
real measurement can be considered.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable

from serial.tools import list_ports

from core.hardware.mega_probe import (
    MEGA_USB_IDS,
    SUPPORTED_MEGA_PROTOCOL,
    MegaProbeInfo,
)


PRUSA_USB_VID = 0x2C99
PRUSA_MK4S_USB_PID = 0x001A


class AcquisitionMode(str, Enum):
    SIMULATION = "simulation"
    DRY_RUN = "dry_run"
    REAL_MEASUREMENT = "real_measurement"


@dataclass(frozen=True)
class UsbPortIdentity:
    device: str
    description: str
    vid: int
    pid: int
    serial_number: str = ""


@dataclass(frozen=True)
class SpmPortMap:
    mk4s: tuple[UsbPortIdentity, ...]
    mega: tuple[UsbPortIdentity, ...]

    @property
    def unambiguous(self) -> bool:
        return len(self.mk4s) == 1 and len(self.mega) == 1


@dataclass(frozen=True)
class SpmReadinessReport:
    port_map: SpmPortMap
    mega_info: MegaProbeInfo | None
    blockers: tuple[str, ...]

    def allows(self, mode: AcquisitionMode) -> bool:
        if mode in {AcquisitionMode.SIMULATION, AcquisitionMode.DRY_RUN}:
            return True
        return not self.blockers

    @property
    def real_measurement_ready(self) -> bool:
        return self.allows(AcquisitionMode.REAL_MEASUREMENT)


def _identity(port: object) -> UsbPortIdentity:
    return UsbPortIdentity(
        device=str(getattr(port, "device", "")),
        description=str(getattr(port, "description", "")),
        vid=int(getattr(port, "vid")),
        pid=int(getattr(port, "pid")),
        serial_number=str(getattr(port, "serial_number", "") or ""),
    )


def discover_spm_ports(ports: Iterable[object] | None = None) -> SpmPortMap:
    """Discover MK4S and plausible Mega USB ports without opening them."""

    available = list(list_ports.comports() if ports is None else ports)
    mk4s: list[UsbPortIdentity] = []
    mega: list[UsbPortIdentity] = []
    for port in available:
        vid = getattr(port, "vid", None)
        pid = getattr(port, "pid", None)
        if (vid, pid) == (PRUSA_USB_VID, PRUSA_MK4S_USB_PID):
            mk4s.append(_identity(port))
        elif (vid, pid) in MEGA_USB_IDS:
            mega.append(_identity(port))
    return SpmPortMap(
        mk4s=tuple(sorted(mk4s, key=lambda item: item.device)),
        mega=tuple(sorted(mega, key=lambda item: item.device)),
    )


def evaluate_spm_readiness(
    port_map: SpmPortMap,
    mega_info: MegaProbeInfo | None = None,
) -> SpmReadinessReport:
    """Return explicit blockers for real measurement."""

    blockers: list[str] = []
    if not port_map.mk4s:
        blockers.append("MK4S USB device not found")
    elif len(port_map.mk4s) > 1:
        blockers.append("multiple MK4S USB devices found")
    if not port_map.mega:
        blockers.append("Arduino Mega CR Touch controller USB device not found")
    elif len(port_map.mega) > 1:
        blockers.append("multiple Arduino Mega candidate USB devices found")

    if mega_info is None:
        blockers.append("Mega CR Touch protocol handshake not completed")
    else:
        if mega_info.identity != "SPM_PROBE_MEGA2560":
            blockers.append(
                f"unsupported Mega probe identity: {mega_info.identity}"
            )
        if mega_info.protocol_version != SUPPORTED_MEGA_PROTOCOL:
            blockers.append(
                f"unsupported Mega probe protocol: {mega_info.protocol_version}"
            )
        if not mega_info.hardware_verified:
            blockers.append("Mega CR Touch hardware commissioning is locked")
        if mega_info.calibration_revision in {"", "NONE", "UNSET"}:
            blockers.append("Mega CR Touch calibration is missing")

    return SpmReadinessReport(port_map, mega_info, tuple(blockers))
