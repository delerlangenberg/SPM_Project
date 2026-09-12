from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CRTouchProbePlan:
    probe_name: str = "CR-Touch contact Z probe"
    trigger_type: str = "digital Hall-effect trigger"
    recommended_tip: str = "rigid steel needle, approximately 1 mm diameter"
    optional_tip: str = "P50/P75 pogo pin with glued 2x2 mm magnet"
    required_magnet: str = "neodymium magnet 2x2 mm; mandatory for pogo pin option"
    guide: str = "PTFE guide tube, 2 mm OD / 1 mm ID, 10-15 mm guide length"
    guide_hole: str = "2.0-2.1 mm guide hole, probe axis vertical"
    needle_length: str = "steel needle cut to approximately 18 mm"
    source_document: str = "CRTouch_SPM_FINAL_Project.docx"
    real_hardware_enabled: bool = False

    def readiness_summary(self) -> str:
        state = "DISABLED" if not self.real_hardware_enabled else "ENABLED"
        return (
            f"{self.probe_name}: {state}\n"
            f"Trigger: {self.trigger_type}\n"
            f"Recommended tip: {self.recommended_tip}\n"
            f"Optional safer tip: {self.optional_tip}\n"
            f"Magnet: {self.required_magnet}\n"
            f"Guide: {self.guide}\n"
            f"Mechanical alignment: {self.guide_hole}\n"
            f"Source: {self.source_document}"
        )

    def safety_summary(self) -> str:
        return (
            "CR-Touch Z probe safety: use slow Z movement, verify repeatable trigger, "
            "avoid hard collisions, and keep the real Z path disabled until wiring, "
            "magnet alignment, and port identity are confirmed."
        )

    def test_sequence_summary(self) -> str:
        return (
            "CR-Touch test sequence: power the sensor, press probe manually, verify "
            "consistent trigger point, adjust magnet position if unstable, and confirm "
            "smooth guide motion without sticking before any software-controlled approach."
        )

    def integration_checklist(self) -> str:
        return (
            "CR-Touch integration checklist:\n"
            "1. Keep real CR-Touch motion disabled until wiring and port identity are confirmed.\n"
            "2. Use the recommended rigid steel needle first for repeatability; pogo pin is safer but less precise.\n"
            "3. Confirm 2x2 mm magnet alignment and smooth PTFE-guided vertical motion.\n"
            "4. Read M119 while pressing the probe manually and verify repeatable trigger/open transitions.\n"
            "5. Only after repeatable manual trigger tests, connect the probe signal to the Z approach feedback path.\n"
            "6. Use slow Z movement and full retract between XY moves."
        )
