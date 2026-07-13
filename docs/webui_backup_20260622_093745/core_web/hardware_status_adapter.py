"""Web-safe adapter for existing SPM hardware information modules.

Phase 2.1H connects the web System STATUS endpoint to the existing
read-only hardware-information layer.

Safety rule:
- no serial connection
- no G-code transmission
- no movement
- dry-run/read-only command plan only
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


SAFE_READONLY_COMMANDS = {
    "IDENTITY": "M115",
    "TEMPERATURE": "M105",
    "ENDSTOPS": "M119",
    "POSITION": "M114",
}


@dataclass(frozen=True)
class WebHardwareInformationStatus:
    available: bool
    source_module: str
    mode: str
    execution_allowed: bool
    gcode_sent: bool
    readonly_actions: dict[str, str]
    command_plan: list[dict[str, str]]
    notes: list[str]


def _load_existing_information_layer() -> tuple[bool, Any | None, list[str]]:
    notes: list[str] = []

    try:
        from core.system import hardware_information_exchange as info_layer
    except Exception as exc:  # pragma: no cover - defensive import boundary
        notes.append(f"hardware_information_exchange import failed: {exc}")
        return False, None, notes

    notes.append("hardware_information_exchange import ok")
    return True, info_layer, notes


def _existing_readonly_actions(info_layer: Any | None) -> dict[str, str]:
    if info_layer is None:
        return dict(SAFE_READONLY_COMMANDS)

    actions = getattr(info_layer, "READONLY_HARDWARE_ACTIONS", None)
    if isinstance(actions, dict):
        return {str(k): str(v) for k, v in actions.items()}

    return dict(SAFE_READONLY_COMMANDS)


def _existing_command_plan(info_layer: Any | None, actions: dict[str, str]) -> list[dict[str, str]]:
    if info_layer is not None and hasattr(info_layer, "action_commands"):
        try:
            commands = info_layer.action_commands("ALL")
            return [
                {"action": str(action), "command": str(command)}
                for action, command in commands
            ]
        except Exception:
            pass

    return [
        {"action": action, "command": command}
        for action, command in actions.items()
    ]


def hardware_information_status() -> dict[str, Any]:
    """Return web-safe read-only hardware information status.

    This intentionally does not call serial transport.
    """
    available, info_layer, notes = _load_existing_information_layer()
    actions = _existing_readonly_actions(info_layer)
    plan = _existing_command_plan(info_layer, actions)

    status = WebHardwareInformationStatus(
        available=available,
        source_module="core.system.hardware_information_exchange",
        mode="dry_run_readonly_plan",
        execution_allowed=False,
        gcode_sent=False,
        readonly_actions=actions,
        command_plan=plan,
        notes=notes
        + [
            "web adapter did not open serial",
            "web adapter did not send G-code",
            "web adapter did not move hardware",
        ],
    )

    return asdict(status)


def validate_readonly_plan(payload: dict[str, Any]) -> bool:
    """Validate that the web-visible plan contains only expected read-only commands."""
    allowed = set(SAFE_READONLY_COMMANDS.values())

    for item in payload.get("command_plan", []):
        command = str(item.get("command", "")).split()[0]
        if command not in allowed:
            return False

    return payload.get("execution_allowed") is False and payload.get("gcode_sent") is False
