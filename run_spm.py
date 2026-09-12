#!/usr/bin/env python3
"""Authoritative Single Application Entrypoint for SPM Prusa Workstation."""

from __future__ import annotations

import os
import sys
from pathlib import Path
import tempfile

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Ensure desktop session has read-only hardware access enabled by default
os.environ.setdefault("SPM_WEB_ALLOW_READONLY_HARDWARE", "1")
if "MPLCONFIGDIR" not in os.environ:
    os.environ["MPLCONFIGDIR"] = os.path.join(tempfile.gettempdir(), "matplotlib_spm")

from PyQt6.QtWidgets import QApplication
from core.application.operator_workstation_software import OperatorWorkstation


def main() -> int:
    app = QApplication(sys.argv)
    window = OperatorWorkstation()
    window.showMaximized()
    print("SPM_WORKSTATION=ACTIVE")
    print("ENTRYPOINT=run_spm.py")
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())

