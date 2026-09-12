from typing import Any, Dict

from .crtouch_driver import CRTouchDriver
from .probe_manager import ProbeManager
from .usb_probe_adapter import USBProbeAdapter


class SensorManager:
    def __init__(self) -> None:
        self.probe_manager = ProbeManager()
        self.usb_adapter = USBProbeAdapter()
        self.probe_manager.register_probe(CRTouchDriver())

    def status(self) -> Dict[str, Any]:
        return {
            "simulation": True,
            "hardware_enabled": False,
            "adapter": self.usb_adapter.status(),
            "active_probe": self.probe_manager.active_status(),
        }

    def connect_probe_system(self) -> Dict[str, Any]:
        adapter_status = self.usb_adapter.connect()
        probe_status = self.probe_manager.active_probe().connect()
        return {
            "simulation": True,
            "hardware_enabled": False,
            "adapter": adapter_status,
            "active_probe": probe_status,
        }

    def disconnect_probe_system(self) -> Dict[str, Any]:
        probe_status = self.probe_manager.active_probe().disconnect()
        adapter_status = self.usb_adapter.disconnect()
        return {
            "simulation": True,
            "hardware_enabled": False,
            "adapter": adapter_status,
            "active_probe": probe_status,
        }

    def read_probe(self) -> Dict[str, Any]:
        return {
            "simulation": True,
            "hardware_enabled": False,
            "adapter_state": self.usb_adapter.read_state(),
            "probe_reading": self.probe_manager.read_active(),
        }
