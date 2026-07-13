import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_stage_2f_dash_dashboard_self_test_passes():
    result = subprocess.run(
        [sys.executable, "tools/stage_2f_dash_probe_dashboard.py", "--self-test"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert "STAGE_2F_DASH_PROBE_DASHBOARD_SELF_TEST_PASSED" in result.stdout


def test_stage_2f_dash_dashboard_does_not_import_or_call_hardware_interfaces():
    text = (ROOT / "tools/stage_2f_dash_probe_dashboard.py").read_text()

    forbidden_patterns = [
        "import serial",
        "serial.Serial",
        "import RPi.GPIO",
        "RPi.GPIO",
        "import gpiozero",
        "GPIO.output",
        "GPIO.input",
        "subprocess.run(['git'",
        "G1 ",
        "M114",
        "M119",
        "M105",
        "M115",
    ]

    for pattern in forbidden_patterns:
        assert pattern not in text

def test_stage_2f_dash_dashboard_contains_operator_safety_language():
    text = (ROOT / "tools/stage_2f_dash_probe_dashboard.py").read_text()

    assert "HARDWARE LOCK ACTIVE" in text
    assert "SPM PC Mode" in text
    assert "hardware may be physically present" in text
    assert "CR Touch direct connection remains blocked" in text
