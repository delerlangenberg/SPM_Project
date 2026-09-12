"""Fail-closed CR Touch mechanical-profile selection."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_mount_profiles(project_root: Path) -> dict[str, Any]:
    path = project_root / "config" / "crtouch_mount_profiles.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    active_name = str(payload.get("active_profile", ""))
    profiles = payload.get("profiles") or {}
    active = profiles.get(active_name)
    if not isinstance(active, dict):
        raise ValueError(f"Unknown active CR Touch mount profile: {active_name!r}")
    return {"name": active_name, "profile": active, "profiles": profiles, "path": path}


def mount_profile_blockers(project_root: Path) -> tuple[str, ...]:
    try:
        loaded = load_mount_profiles(project_root)
    except Exception as exc:
        return (f"CR Touch mount profile is unreadable: {exc}",)
    profile = loaded["profile"]
    blockers: list[str] = []
    if not profile.get("enabled"):
        blockers.append(
            f"CR Touch mount profile {loaded['name']!r} is locked: "
            f"{profile.get('commissioning_status', 'NOT_COMMISSIONED')}."
        )
    envelope = profile.get("native_scan_envelope_mm")
    if not isinstance(envelope, dict):
        blockers.append("The active CR Touch mount has no verified XY scan envelope.")
    if profile.get("local_bare_stage_trigger_z_mm") is None:
        blockers.append("The active CR Touch mount has no verified bare-stage Z reference.")
    if profile.get("safe_travel_z_mm") is None:
        blockers.append("The active CR Touch mount has no verified safe travel Z.")
    return tuple(blockers)
