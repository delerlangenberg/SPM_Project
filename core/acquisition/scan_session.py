from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from core.education.scan_profile import ScanProfile


def build_scan_session_metadata(
    *,
    profile: ScanProfile,
    output_file: str,
    point_count: int,
    execution_mode: str,
    channel: str,
) -> dict:
    return {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "execution_mode": execution_mode,
        "channel": channel,
        "output_file": output_file,
        "point_count": point_count,
        "scan_profile": asdict(profile),
    }


def metadata_path_for_output(output_file: str) -> Path:
    return Path(output_file).with_suffix(".metadata.json")


def write_scan_session_metadata(
    *,
    profile: ScanProfile,
    output_file: str,
    point_count: int,
    execution_mode: str,
    channel: str,
) -> Path:
    path = metadata_path_for_output(output_file)
    path.parent.mkdir(parents=True, exist_ok=True)
    metadata = build_scan_session_metadata(
        profile=profile,
        output_file=output_file,
        point_count=point_count,
        execution_mode=execution_mode,
        channel=channel,
    )
    path.write_text(
        json.dumps(metadata, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return path
