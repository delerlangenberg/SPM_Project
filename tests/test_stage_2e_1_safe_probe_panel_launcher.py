import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_stage_2e_safe_probe_panel_launcher_passes():
    result = subprocess.run(
        [sys.executable, "tools/stage_2e_safe_probe_panel_launcher.py"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert "STAGE_2E_SAFE_PROBE_PANEL_LAUNCHER_PASSED" in result.stdout
    assert "Hardware: blocked" in result.stdout
    assert "Serial: disabled" in result.stdout
    assert "GPIO: disabled" in result.stdout
    assert "G-code: disabled" in result.stdout
    assert "Active probe: 001 / cr_touch" in result.stdout
    assert "SIMULATION ONLY - hardware access blocked" in result.stdout
