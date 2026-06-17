"""Launch the local SPM Prusa web operator console.

This launcher is intentionally safe to run directly from tools/.
It inserts the project root into sys.path before importing core.web.
"""

from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.web.operator_console_server import main  # noqa: E402


if __name__ == "__main__":
    main()
