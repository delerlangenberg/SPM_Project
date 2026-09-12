"""Host-side command policy for a future nozzle-removed scanner profile."""

from __future__ import annotations

import re

READ_ONLY = frozenset({"M105", "M114", "M115", "M119"})
MOTION_CONTROL = frozenset({"G0", "G1", "G90", "G91", "M17", "M18", "M400"})
ALWAYS_BLOCKED = frozenset(
    {
        "G10", "G11", "G29",
        "M24", "M25",
        "M82", "M83",
        "M109", "M190",
        "M302", "M600", "M701", "M702",
    }
)


def command_word(command: str) -> str:
    text = command.split(";", 1)[0].strip().upper()
    return text.split(maxsplit=1)[0] if text else ""


def centered_scanner_command_blocker(command: str) -> str | None:
    """Return a fail-closed reason, or None for the small scanner subset."""

    text = command.split(";", 1)[0].strip().upper()
    word = command_word(text)
    if not word:
        return "Empty command is not permitted."
    if word in ALWAYS_BLOCKED:
        return f"{word} is disabled in centered scanner mode."
    if word == "G28":
        axes = text.split()[1:]
        if axes and all(axis in {"X", "Y"} for axis in axes):
            return None
        return "G28 is restricted to explicit X and/or Y homing in centered scanner mode."
    if word in {"M104", "M140"}:
        if re.fullmatch(rf"{word}\s+S0(?:\.0+)?", text):
            return None
        return f"{word} may only set S0 in centered scanner mode."
    if word == "M107":
        return None
    if word not in READ_ONLY | MOTION_CONTROL:
        return f"{word} is outside the centered scanner command allowlist."
    if word in {"G0", "G1"}:
        if re.search(r"(?:^|\s)E[-+]?\d", text):
            return "Extruder-axis movement is disabled in centered scanner mode."
        if not re.search(r"(?:^|\s)[XYZ][-+]?\d", text):
            return "A centered scanner move must contain X, Y or Z."
    return None
