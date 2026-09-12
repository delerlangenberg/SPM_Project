"""Public connection manager interface for the SPM Operator."""

from .manager import ConnectionManager, ConnectionStatus
from .serial_handler import SerialPortInfo, discover_ports

__all__ = ["ConnectionManager", "ConnectionStatus", "SerialPortInfo", "discover_ports"]

