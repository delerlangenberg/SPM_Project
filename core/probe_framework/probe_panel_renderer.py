from typing import List

from .probe_status_panel_model import ProbeStatusPanelModel


class ProbePanelRenderer:
    def __init__(self) -> None:
        self.model = ProbeStatusPanelModel()

    def render_text_panel(self) -> str:
        lines: List[str] = []
        lines.append("========================================")
        lines.append(" SPM Probe System Panel")
        lines.append("========================================")
        lines.extend(self.model.status_lines())
        lines.append("")
        lines.append("Blocked interfaces:")
        for item in self.model.snapshot()["blocked_interfaces"]:
            lines.append(f"  - {item}")
        lines.append("========================================")
        return "\n".join(lines)
