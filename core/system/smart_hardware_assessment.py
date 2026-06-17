"""Local smart assessment for the Educational SPM hardware-test layer."""

from __future__ import annotations

import re
from dataclasses import dataclass

from core.system.hardware_information_exchange import HardwareInformationResult
from core.system.hardware_test_controls import LIMITS


@dataclass(frozen=True)
class SmartHardwareAssessment:
    readiness: str
    score: int
    recommendation: str
    details: list[str]
    position: dict[str, float] | None


def extract_xyz(response_lines: list[str]) -> dict[str, float] | None:
    joined = " | ".join(response_lines)
    match = re.search(r"X:\s*(-?\d+(?:\.\d+)?)\s+Y:\s*(-?\d+(?:\.\d+)?)\s+Z:\s*(-?\d+(?:\.\d+)?)", joined)
    if not match:
        return None
    x_value, y_value, z_value = match.groups()
    return {"x": float(x_value), "y": float(y_value), "z": float(z_value)}


def _position_inside_limits(position: dict[str, float]) -> bool:
    for axis, value in position.items():
        low, high = LIMITS[axis]
        if value < low or value > high:
            return False
    return True


def assess_hardware_information(results: list[HardwareInformationResult]) -> SmartHardwareAssessment:
    by_action = {result.action: result for result in results}
    details: list[str] = []
    score = 0
    position: dict[str, float] | None = None

    identity = by_action.get("IDENTITY")
    if identity and identity.success:
        score += 25
        firmware = next((line for line in identity.response_lines if "FIRMWARE_NAME" in line), "identity received")
        details.append(f"Controller identity OK: {firmware[:100]}")
    else:
        details.append("Controller identity missing or incomplete.")

    temperature = by_action.get("TEMPERATURE")
    if temperature and temperature.success:
        score += 20
        details.append("Temperature/status channel OK.")
    else:
        details.append("Temperature/status channel missing or incomplete.")

    endstops = by_action.get("ENDSTOPS")
    endstop_text = " | ".join(endstops.response_lines).lower() if endstops else ""
    if endstops and endstops.success and "triggered" not in endstop_text:
        score += 25
        details.append("Endstops report open.")
    elif endstops and endstops.success:
        score += 10
        details.append("One or more endstops appear triggered. Check the printer before motion.")
    else:
        details.append("Endstop state was not confirmed.")

    position_result = by_action.get("POSITION")
    if position_result and position_result.success:
        position = extract_xyz(position_result.response_lines)
        if position and _position_inside_limits(position):
            score += 30
            details.append(
                f"XYZ position inside confirmed limits: X={position['x']:.2f}, Y={position['y']:.2f}, Z={position['z']:.2f}."
            )
        elif position:
            score += 10
            details.append("XYZ position was read, but one axis is outside the confirmed software limits.")
        else:
            details.append("Position command responded, but XYZ coordinates were not parsed.")
    else:
        details.append("XYZ position was not confirmed.")

    if score >= 90:
        readiness = "READY_FOR_SUPERVISED_MOTION"
        recommendation = "Connection looks healthy. Next: run one supervised 1-5 mm test step while watching the MK4S."
    elif score >= 60:
        readiness = "CHECK_BEFORE_MOTION"
        recommendation = "Partial communication is working. Repeat the smart check and inspect the missing channel before movement."
    else:
        readiness = "NOT_READY"
        recommendation = "Do not move hardware yet. Check USB, power, COM5, and MK4S status, then run Smart System Check again."

    return SmartHardwareAssessment(
        readiness=readiness,
        score=score,
        recommendation=recommendation,
        details=details,
        position=position,
    )
