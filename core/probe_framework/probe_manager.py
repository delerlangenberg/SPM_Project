from typing import Dict, List, Optional

from .probe_base import ProbeBase


class ProbeManager:
    def __init__(self) -> None:
        self._probes: Dict[str, ProbeBase] = {}
        self._active_probe_id: Optional[str] = None

    def register_probe(self, probe: ProbeBase) -> None:
        probe_id = probe.identity.probe_id
        self._probes[probe_id] = probe
        if self._active_probe_id is None:
            self._active_probe_id = probe_id

    def list_probes(self) -> List[dict]:
        return [probe.identify() for probe in self._probes.values()]

    def set_active_probe(self, probe_id: str) -> dict:
        if probe_id not in self._probes:
            raise KeyError(f"Unknown probe_id: {probe_id}")
        self._active_probe_id = probe_id
        return self.active_probe().identify()

    def active_probe(self) -> ProbeBase:
        if self._active_probe_id is None:
            raise RuntimeError("No active probe registered")
        return self._probes[self._active_probe_id]

    def active_status(self) -> dict:
        return self.active_probe().status()

    def read_active(self) -> dict:
        return self.active_probe().read()
