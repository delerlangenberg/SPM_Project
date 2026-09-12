from typing import Dict, List

from .workstation_probe_contract import WorkstationProbeContract


class ProbeStatusPanelModel:
    def __init__(self) -> None:
        self.contract = WorkstationProbeContract()

    def snapshot(self) -> Dict[str, object]:
        setup = self.contract.setup_summary()
        active = setup["active_probe"]
        adapter = setup["adapter"]

        return {
            "title": "Probe System",
            "stage": "Stage 2D.1",
            "active_probe_label": f'{active["probe_id"]} / {active["kind"]}',
            "probe_connected": active["connected"],
            "probe_deployed": active["deployed"],
            "adapter_port": adapter["port"],
            "adapter_connected": adapter["connected"],
            "hardware_enabled": False,
            "simulation": True,
            "blocked_interfaces": setup["blocked_interfaces"],
            "status_text": "SIMULATION ONLY - hardware access blocked",
        }

    def status_lines(self) -> List[str]:
        snap = self.snapshot()
        return [
            f'Panel: {snap["title"]}',
            f'Stage: {snap["stage"]}',
            f'Active probe: {snap["active_probe_label"]}',
            f'Probe connected: {snap["probe_connected"]}',
            f'Probe deployed: {snap["probe_deployed"]}',
            f'Adapter port: {snap["adapter_port"]}',
            f'Adapter connected: {snap["adapter_connected"]}',
            f'Hardware enabled: {snap["hardware_enabled"]}',
            f'Simulation: {snap["simulation"]}',
            f'Status: {snap["status_text"]}',
        ]
