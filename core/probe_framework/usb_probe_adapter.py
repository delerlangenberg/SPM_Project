from typing import Any, Dict, List


class USBProbeAdapter:
    def __init__(self, port: str = "SIMULATED_USB_PROBE") -> None:
        self.port = port
        self.connected = False
        self.hardware_enabled = False
        self._events: List[str] = []

    def connect(self) -> Dict[str, Any]:
        self.connected = True
        self._events.append("connect_simulated")
        return self.status()

    def disconnect(self) -> Dict[str, Any]:
        self.connected = False
        self._events.append("disconnect_simulated")
        return self.status()

    def write_command(self, command: str) -> Dict[str, Any]:
        self._events.append(f"blocked_command:{command}")
        return {
            "accepted": False,
            "blocked": True,
            "command": command,
            "reason": "Stage 2B simulation only",
        }

    def read_state(self) -> Dict[str, Any]:
        return {
            "port": self.port,
            "connected": self.connected,
            "simulation": True,
            "triggered": False,
            "value": 0.0,
        }

    def status(self) -> Dict[str, Any]:
        return {
            "port": self.port,
            "connected": self.connected,
            "hardware_enabled": False,
            "simulation": True,
        }

    def event_history(self) -> List[str]:
        return list(self._events)
