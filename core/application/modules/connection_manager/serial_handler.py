"""Serial discovery isolated from connection state and the PyQt interface."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable, Any


@dataclass(frozen=True, slots=True)
class SerialPortInfo:
    device: str
    description: str = ""
    hardware_id: str = ""


def discover_ports(provider: Callable[[], Iterable[Any]] | None = None) -> tuple[SerialPortInfo, ...]:
    """Return deterministic serial-port metadata without opening any device."""
    from pathlib import Path

    custom_provider = provider is not None
    if provider is None:
        from serial.tools import list_ports
        provider = list_ports.comports

    discovered: list[SerialPortInfo] = []

    # Prioritize verified Stage 4 SPM hardware aliases when scanning real system
    if not custom_provider:
        if Path("/dev/spm-mk4s").exists():
            discovered.append(
                SerialPortInfo(
                    device="/dev/spm-mk4s",
                    description="Original Prusa MK4S (SPM Alias)",
                    hardware_id="Prusa Buddy 6.2.4+8909",
                )
            )
        if Path("/dev/spm-arduino").exists():
            discovered.append(
                SerialPortInfo(
                    device="/dev/spm-arduino",
                    description="Arduino Mega 2560 (SPM Probe Alias)",
                    hardware_id="CR-Touch Fast-Tap 0.8.7",
                )
            )

    seen = {p.device for p in discovered}
    for item in provider():
        dev = str(getattr(item, "device", "")).strip()
        if not dev or dev in seen:
            continue
        desc = str(getattr(item, "description", "") or "")
        hwid = str(getattr(item, "hwid", "") or "")
        # Filter unconfigured ttyS platform UARTs
        if dev.startswith("/dev/ttyS") and (desc == "n/a" or not desc):
            continue
        discovered.append(
            SerialPortInfo(
                device=dev,
                description=desc,
                hardware_id=hwid,
            )
        )
        seen.add(dev)

    if custom_provider:
        return tuple(sorted(discovered, key=lambda item: item.device.casefold()))
    return tuple(discovered)


