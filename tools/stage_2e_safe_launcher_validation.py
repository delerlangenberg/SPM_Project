import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

TESTS = [
    "tests/test_stage_2c_1_workstation_probe_contract.py",
    "tests/test_stage_2c_2_probe_status_cli.py",
    "tests/test_stage_2d_1_probe_status_panel_model.py",
    "tests/test_stage_2d_2_probe_panel_renderer.py",
    "tests/test_stage_2e_1_safe_probe_panel_launcher.py",
]


def run_command(command: list[str]) -> int:
    print("RUNNING:")
    print(" ".join(command))
    result = subprocess.run(command, cwd=ROOT)
    return result.returncode


def main() -> int:
    print("=== STAGE 2E SAFE LAUNCHER VALIDATION ===")
    print(f"ROOT: {ROOT}")

    missing = [path for path in TESTS if not (ROOT / path).exists()]
    if missing:
        print("MISSING_TESTS:")
        for path in missing:
            print(f"- {path}")
        print("STAGE_2E_SAFE_LAUNCHER_VALIDATION_FAILED")
        return 1

    test_command = [sys.executable, "-m", "pytest", "-q", *TESTS]
    if run_command(test_command) != 0:
        print("STAGE_2E_SAFE_LAUNCHER_VALIDATION_FAILED")
        return 1

    launcher_command = [sys.executable, "tools/stage_2e_safe_probe_panel_launcher.py"]
    if run_command(launcher_command) != 0:
        print("STAGE_2E_SAFE_LAUNCHER_VALIDATION_FAILED")
        return 1

    print("STAGE_2E_SAFE_LAUNCHER_VALIDATION_PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
