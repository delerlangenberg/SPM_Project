"""Academic AI advisory layer for the SPM Prusa project.

This module is intentionally conservative.

Academic AI may suggest, explain, diagnose, and simulate.
It must not directly execute MK4S motion commands.
Real movement must always pass through local safety gates and operator confirmation.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AcademicAIStatus:
    configured: bool
    mode: str
    role: str
    safety_rule: str


def get_academic_ai_status() -> AcademicAIStatus:
    """Return current Academic AI integration status without exposing secrets."""
    base_url = os.getenv("ACADEMIC_AI_BASE_URL", "").strip()
    api_key = os.getenv("ACADEMIC_AI_API_KEY", "").strip()
    model_or_assistant = os.getenv("ACADEMIC_AI_MODEL", "").strip() or os.getenv("ACADEMIC_AI_ASSISTANT_ID", "").strip()

    configured = bool(base_url and api_key and model_or_assistant)

    return AcademicAIStatus(
        configured=configured,
        mode="configured" if configured else "stub_not_configured",
        role="advisory_only",
        safety_rule="AI may recommend approach, scan, simulation, or diagnosis steps, but cannot execute machine motion directly.",
    )


def build_ai_recommendation(task: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
    """Build a safe advisory response.

    Phase 2.2 is a shell. It returns deterministic local recommendations.
    Later phases can connect this function to Academic AI API credentials.
    """
    context = context or {}
    normalized = task.strip().lower()
    status = get_academic_ai_status()

    if "approach" in normalized or "z" in normalized:
        recommendation = [
            "Confirm MK4S position readback before any Z move.",
            "Use dry-run or simulation mode first.",
            "Use small Z steps near the surface.",
            "Require operator confirmation before real motion.",
            "Log every approach/retract command.",
        ]
        risk = "high"
        target_phase = "2.3"
    elif "scan" in normalized or "xy" in normalized or "raster" in normalized:
        recommendation = [
            "Start with a small scan area inside the safe XY envelope.",
            "Use low resolution first, for example 5x5 or 10x10.",
            "Preview the raster path before real movement.",
            "Generate CSV and PNG output before connecting live hardware.",
            "Only enable real scan after Z and XY status are valid.",
        ]
        risk = "medium"
        target_phase = "2.4"
    elif "simulation" in normalized or "surface" in normalized or "demo" in normalized:
        recommendation = [
            "Use the simulation layer to generate expected topography first.",
            "Keep simulation parameters separate from real hardware parameters.",
            "Use the same scan profile for simulation and real scan comparison.",
            "Show simulation output in the Live View window.",
        ]
        risk = "low"
        target_phase = "2.4"
    else:
        recommendation = [
            "Use Academic AI as an explanation and planning assistant.",
            "Keep all physical motion under local safety control.",
            "Ask for a recommendation, then let the operator approve any action.",
        ]
        risk = "low"
        target_phase = "2.2"

    return {
        "ai_mode": status.mode,
        "role": status.role,
        "task": task,
        "target_phase": target_phase,
        "risk": risk,
        "recommendation": recommendation,
        "context_received": context,
        "execution_allowed": False,
        "safety_note": status.safety_rule,
    }
