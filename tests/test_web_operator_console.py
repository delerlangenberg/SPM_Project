from pathlib import Path

from core.web.operator_console_server import PHASE_MAP, WEB_ROOT, json_response


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_web_operator_console_files_exist():
    assert (WEB_ROOT / "index.html").exists()
    assert (WEB_ROOT / "style.css").exists()
    assert (WEB_ROOT / "app.js").exists()


def test_web_operator_console_layout_contains_required_sections():
    html = (WEB_ROOT / "index.html").read_text(encoding="utf-8")

    required = [
        "Educational SPM - Prusa MK4S",
        "View",
        "Tools",
        "Open",
        "About",
        "Main System",
        "Z Scanner",
        "XY Scanner",
        "X-",
        "X+",
        "Y-",
        "Y+",
        "Phase 2.1",
        "Phase 2.2",
        "Phase 2.3",
        "Phase 2.4",
        "Phase 2.5",
    ]

    for marker in required:
        assert marker in html


def test_phase_map_labels_future_integration_work():
    phases = {item["phase"]: item for item in PHASE_MAP}

    assert phases["2.0"]["status"] == "implemented"
    assert "System power" in phases["2.1"]["name"]
    assert "Z scanner" in phases["2.2"]["name"]
    assert "XY scanner" in phases["2.3"]["name"]
    assert "Live scan" in phases["2.4"]["name"]
    assert "operator workflow" in phases["2.5"]["name"]


def test_json_response_serializes_api_payload():
    payload = {"status": "ok", "phase": "2.0"}
    body = json_response(payload)
    assert b'"status": "ok"' in body
    assert b'"phase": "2.0"' in body

def test_web_operator_console_launcher_help_runs():
    import subprocess
    import sys

    result = subprocess.run(
        [sys.executable, "tools/run_web_operator_console.py", "--help"],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        timeout=10,
    )

    assert result.returncode == 0
    assert "Run the local SPM Prusa web operator console" in result.stdout
