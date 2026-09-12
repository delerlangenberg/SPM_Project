"""One-button initialization orchestration for the main SPM workstation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from core.system.hardware_diagnostics import HardwareDiagnosticReport, run_hardware_communication_report
from core.system.hardware_information_exchange import HardwareInformationResult, run_real_information_exchange
from core.system.smart_hardware_assessment import SmartHardwareAssessment, assess_hardware_information


@dataclass(frozen=True)
class WorkstationInitializationResult:
    passed: bool
    ready_state: str
    recommendation: str
    diagnostic_report: HardwareDiagnosticReport
    assessment: SmartHardwareAssessment
    z_ready: bool
    summary_lines: list[str]


def run_workstation_initialization(
    config: dict,
    z_driver,
    *,
    diagnostic_runner: Callable[[dict], HardwareDiagnosticReport] = run_hardware_communication_report,
    information_runner: Callable[[str], list[HardwareInformationResult]] = run_real_information_exchange,
) -> WorkstationInitializationResult:
    """Run the main one-button no-motion hardware initialization.

    This performs real read-only MK4S communication checks and prepares the
    current dry-run Z scanner layer. It does not enable real motion.
    """

    diagnostic_report = diagnostic_runner(config)
    information_results = information_runner("ALL")
    assessment = assess_hardware_information(information_results)

    z_ready = False
    if not getattr(z_driver, "connected", False):
        z_ready = bool(z_driver.connect())
    else:
        z_ready = True

    passed = diagnostic_report.passed and assessment.readiness == "READY_FOR_SUPERVISED_MOTION" and z_ready
    ready_state = "SYSTEM READY" if passed else "INITIALIZATION FAILED"
    recommendation = (
        "System ready. Next: use Z Scanner controls for manual move, auto approach, or retract."
        if passed
        else assessment.recommendation
    )
    summary_lines = [
        f"Initialization: {ready_state}",
        f"Hardware diagnostic: {'PASS' if diagnostic_report.passed else 'FAIL'}",
        f"Self assessment: {assessment.readiness} ({assessment.score}/100)",
        f"Z scanner layer: {'READY' if z_ready else 'NOT READY'}",
        f"Recommendation: {recommendation}",
    ]
    summary_lines.extend(diagnostic_report.summary_lines())
    summary_lines.extend(f"Assessment: {detail}" for detail in assessment.details)

    return WorkstationInitializationResult(
        passed=passed,
        ready_state=ready_state,
        recommendation=recommendation,
        diagnostic_report=diagnostic_report,
        assessment=assessment,
        z_ready=z_ready,
        summary_lines=summary_lines,
    )
