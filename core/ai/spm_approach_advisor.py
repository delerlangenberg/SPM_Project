from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ApproachAdvisorInput:
    z_setpoint_mm: float
    tapping_range_mm: float
    expected_surface_z_mm: float
    approach_speed_mm_s: float
    full_retract_z_mm: float
    latest_z_mm: float
    connected: bool = False

    @property
    def tap_start_z_mm(self) -> float:
        return self.z_setpoint_mm + self.tapping_range_mm


def advise_approach(settings: ApproachAdvisorInput) -> dict[str, object]:
    issues: list[str] = []
    recommendations: list[str] = []
    risk = "ready"

    if not settings.connected:
        issues.append("System is not connected.")
        recommendations.append("Connect Phase 2.1 before any real Z approach or tapping scan.")
        risk = "blocked"

    if settings.tapping_range_mm <= 0:
        issues.append("Tapping range must be positive.")
        recommendations.append("Set a positive tapping range so the scan has a real Z search window.")
        risk = "blocked"

    if settings.expected_surface_z_mm > 0:
        if settings.z_setpoint_mm > settings.expected_surface_z_mm:
            issues.append(
                f"Z setpoint {settings.z_setpoint_mm:.3f} mm is above expected surface "
                f"{settings.expected_surface_z_mm:.3f} mm."
            )
            recommendations.append("Lower the Z setpoint/contact limit below the expected surface height.")
            risk = "blocked"
        if settings.tap_start_z_mm <= settings.expected_surface_z_mm:
            issues.append(
                f"Tap start Z {settings.tap_start_z_mm:.3f} mm is at/below expected surface "
                f"{settings.expected_surface_z_mm:.3f} mm."
            )
            recommendations.append("Increase tapping range or raise the setpoint so approach starts above the sample.")
            risk = "blocked"

    if settings.full_retract_z_mm < settings.tap_start_z_mm:
        issues.append(
            f"Full retract Z {settings.full_retract_z_mm:.3f} mm is below tap start "
            f"{settings.tap_start_z_mm:.3f} mm."
        )
        recommendations.append("Set full retract Z at or above the tap start height.")
        risk = "blocked"

    if settings.approach_speed_mm_s > 10.0:
        issues.append(f"Approach speed {settings.approach_speed_mm_s:.3f} mm/s is aggressive near contact.")
        recommendations.append("Use 0.2..2.0 mm/s while the contact feedback path is experimental.")
        risk = "blocked" if risk == "blocked" else "caution"
    elif settings.approach_speed_mm_s > 2.0:
        issues.append(f"Approach speed {settings.approach_speed_mm_s:.3f} mm/s is above the conservative test range.")
        recommendations.append("For first contact tests, reduce approach speed to 2.0 mm/s or lower.")
        risk = "caution" if risk == "ready" else risk

    if settings.latest_z_mm < settings.tap_start_z_mm:
        issues.append(
            f"Current Z {settings.latest_z_mm:.3f} mm is below tap start {settings.tap_start_z_mm:.3f} mm."
        )
        recommendations.append("Retract or read/verify Z before starting an approach sequence.")
        risk = "caution" if risk == "ready" else risk

    if not issues:
        recommendations.append(
            "Approach window is coherent: start above expected surface, search down through the surface, then retract."
        )
        recommendations.append("For real tapping, watch hardware continuously and keep STOP Z available.")

    return {
        "ok": risk != "blocked",
        "risk": risk,
        "tap_start_z_mm": settings.tap_start_z_mm,
        "tap_min_z_mm": settings.z_setpoint_mm,
        "expected_surface_z_mm": settings.expected_surface_z_mm,
        "issues": issues,
        "recommendations": recommendations,
        "summary": (
            f"Approach advisor: {risk}. Search Z {settings.tap_start_z_mm:.3f} -> "
            f"{settings.z_setpoint_mm:.3f} mm; expected surface {settings.expected_surface_z_mm:.3f} mm."
        ),
    }
