from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.education.config_loader import load_config
from core.motion.parking import park_mk4s


def main() -> int:
    state = park_mk4s(load_config())
    print("MK4S parked:", state)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
