"""Read-only evidence and safe-output policy for the converted MK4S scanner."""

from __future__ import annotations

from dataclasses import dataclass
import re


@dataclass(frozen=True)
class Stage2ThermalState:
    nozzle_actual_c: float
    nozzle_target_c: float
    bed_actual_c: float
    bed_target_c: float
    nozzle_output: int
    bed_output: int

    @property
    def removed_hotend_is_inactive(self) -> bool:
        return (
            self.nozzle_actual_c <= -10.0
            and self.nozzle_target_c == 0.0
            and self.nozzle_output == 0
            and self.bed_target_c == 0.0
            and self.bed_output == 0
        )


def parse_m105(line: str) -> Stage2ThermalState:
    patterns = {
        "nozzle_actual_c": r"\bT:([-\d.]+)/",
        "nozzle_target_c": r"\bT:[-\d.]+/([-\d.]+)",
        "bed_actual_c": r"\bB:([-\d.]+)/",
        "bed_target_c": r"\bB:[-\d.]+/([-\d.]+)",
        "nozzle_output": r"(?:^|\s)@:([-\d]+)",
        "bed_output": r"\bB@:([-\d]+)",
    }
    values: dict[str, float | int] = {}
    for name, pattern in patterns.items():
        match = re.search(pattern, line)
        if not match:
            raise ValueError(f"M105 field missing: {name}")
        values[name] = (
            int(match.group(1))
            if name.endswith("output")
            else float(match.group(1))
        )
    return Stage2ThermalState(**values)


STAGE2_OUTPUT_OFF_COMMANDS = ("M104 S0", "M140 S0", "M107")


def stage2_thermal_blockers(m105_line: str) -> tuple[str, ...]:
    """Require positive evidence that every removed-tool thermal output is off."""

    try:
        state = parse_m105(m105_line)
    except ValueError as exc:
        return (f"Stage 2 thermal state is unreadable: {exc}",)
    blockers: list[str] = []
    if state.nozzle_actual_c > -10.0:
        blockers.append(
            "Removed hotend thermistor does not read open/cold (expected <= -10 C)."
        )
    if state.nozzle_target_c != 0.0 or state.nozzle_output != 0:
        blockers.append("Nozzle heater target/output is not zero.")
    if state.bed_target_c != 0.0 or state.bed_output != 0:
        blockers.append("Bed heater target/output is not zero.")
    return tuple(blockers)
