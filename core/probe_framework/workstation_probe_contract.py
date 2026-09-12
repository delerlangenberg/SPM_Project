from typing import Any, Dict

from .hardware_presence import serial_port_snapshot
from .sensor_manager import SensorManager


class WorkstationProbeContract:
    """
    Safe workstation-facing contract for the probe framework.

    This is the only object the workstation/UI should use at this stage.
    It exposes probe setup, status, connect, disconnect, and read operations
    while keeping all hardware access simulated or blocked.
    """

    def __init__(self) -> None:
        self.sensor_manager = SensorManager()

    def setup_summary(self) -> Dict[str, Any]:
        status = self.sensor_manager.status()
        return {
            "stage": "Stage 2C.1",
            "contract": "WorkstationProbeContract",
            "purpose": "Safe workstation-facing probe interface",
            "simulation": True,
            "hardware_enabled": False,
            "active_probe": status["active_probe"],
            "adapter": status["adapter"],
            "blocked_interfaces": [
                "hardware_motion",
                "serial_hardware",
                "gpio",
                "gcode",
                "prusa_firmware_modification",
            ],
        }

    def status(self) -> Dict[str, Any]:
        return self.sensor_manager.status()

    def connect(self) -> Dict[str, Any]:
        return self.sensor_manager.connect_probe_system()

    def disconnect(self) -> Dict[str, Any]:
        return self.sensor_manager.disconnect_probe_system()

    def read(self) -> Dict[str, Any]:
        return self.sensor_manager.read_probe()

    def hardware_presence_summary(self) -> Dict[str, Any]:
        """Return serial port snapshot for UI display. No hardware is opened."""
        return serial_port_snapshot()
