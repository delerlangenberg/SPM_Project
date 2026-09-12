"""SPM Operator Interface version information."""

from __future__ import annotations

from datetime import datetime
import subprocess
from pathlib import Path

VERSION_MAJOR = 1
VERSION_MINOR = 3
VERSION_PATCH = 1
VERSION_BUILD = 0
VERSION_DATE = "20260731"

FULL_VERSION = f"{VERSION_MAJOR}.{VERSION_MINOR}.{VERSION_PATCH}.{VERSION_BUILD}"
VERSION_STRING = f"v{FULL_VERSION}-{VERSION_DATE}"
VERSION_DISPLAY = f"SPM Operator v{VERSION_MAJOR}.{VERSION_MINOR}.{VERSION_PATCH} (Build {VERSION_BUILD})"
BUILD_DATE_DISPLAY = datetime.strptime(VERSION_DATE, "%Y%m%d").strftime("%Y-%m-%d")


def git_build_id(project_root: Path | None = None) -> str:
    """Return the short source revision, or ``unknown`` outside a Git checkout."""
    root = project_root or Path(__file__).resolve().parents[2]
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short=7", "HEAD"],
            cwd=root,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.SubprocessError):
        return "unknown"
