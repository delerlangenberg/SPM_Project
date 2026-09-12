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
    if provider is None:
        from serial.tools import list_ports

        provider = list_ports.comports
    ports = (
        SerialPortInfo(
            device=str(item.device),
            description=str(getattr(item, "description", "") or ""),
            hardware_id=str(getattr(item, "hwid", "") or ""),
        )
        for item in provider()
        if str(getattr(item, "device", "")).strip()
    )
    return tuple(sorted(ports, key=lambda item: item.device.casefold()))

