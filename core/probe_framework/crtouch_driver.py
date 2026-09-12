from typing import Any, Dict

from .probe_base import ProbeBase
from .probe_types import ProbeIdentity, ProbeKind


class CRTouchDriver(ProbeBase):
    def __init__(self) -> None:
        super().__init__(
            ProbeIdentity(
                probe_id="001",
                kind=ProbeKind.CR_TOUCH,
                name="CR Touch simulated probe",
                hardware_enabled=False,
            )
        )
        self.deployed = False

    def connect(self) -> Dict[str, Any]:
        self.connected = True
        return self.status()

    def disconnect(self) -> Dict[str, Any]:
        self.connected = False
        self.deployed = False
        return self.status()

    def deploy(self) -> Dict[str, Any]:
        self.deployed = True
        return self.status()

    def retract(self) -> Dict[str, Any]:
        self.deployed = False
        return self.status()

    def read(self) -> Dict[str, Any]:
        return {"triggered": False, "value": 0.0, "simulation": True}

    def calibrate(self) -> Dict[str, Any]:
        return {"calibrated": True, "simulation": True}

    def status(self) -> Dict[str, Any]:
        return {
            "probe_id": self.identity.probe_id,
            "kind": self.identity.kind.value,
            "connected": self.connected,
            "deployed": self.deployed,
            "hardware_enabled": False,
            "simulation": True,
        }

    def identify(self) -> Dict[str, Any]:
        return {
            "probe_id": self.identity.probe_id,
            "kind": self.identity.kind.value,
            "name": self.identity.name,
        }
