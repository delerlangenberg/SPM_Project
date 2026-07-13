import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.probe_framework import ProbePanelRenderer


def main() -> int:
    print("=== STAGE 2E SAFE PROBE PANEL LAUNCHER ===")
    print(f"ROOT: {ROOT}")
    print("Mode: standalone")
    print("Hardware: blocked")
    print("Serial: disabled")
    print("GPIO: disabled")
    print("G-code: disabled")
    print("")

    renderer = ProbePanelRenderer()
    print(renderer.render_text_panel())

    print("")
    print("STAGE_2E_SAFE_PROBE_PANEL_LAUNCHER_PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
