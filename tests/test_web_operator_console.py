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

def test_web_operator_console_main_page_is_not_roadmap_page():
    html = (WEB_ROOT / "index.html").read_text(encoding="utf-8")

    assert "phase-roadmap" not in html
    assert "Integration Roadmap" not in html
    assert "id=\"phase-map\"" not in html


def test_web_operator_console_has_floating_scan_and_live_windows():
    html = (WEB_ROOT / "index.html").read_text(encoding="utf-8")

    required = [
        "id=\"scan-window\"",
        "Scan Setup Window",
        "id=\"live-window\"",
        "Live View / Measurement Window",
        "id=\"status-window\"",
        "System Status Window",
        "id=\"about-window\"",
        "data-open-window=\"scan-window\"",
        "data-open-window=\"live-window\"",
    ]

    for marker in required:
        assert marker in html


def test_web_operator_console_main_page_keeps_essential_controls():
    html = (WEB_ROOT / "index.html").read_text(encoding="utf-8")

    required = [
        "Main System",
        "Z Scanner",
        "XY Jog Control",
        "Status / Live Log",
        "ON",
        "OFF",
        "STATUS",
        "CLOSE",
        "Approach",
        "Retract",
        "Read Z",
        "Park Z",
        "X-",
        "X+",
        "Y-",
        "Y+",
        "CENTER",
    ]

    for marker in required:
        assert marker in html

def test_academic_ai_advisory_status_is_safe_by_default(monkeypatch):
    from core.ai.academic_ai_client import get_academic_ai_status

    monkeypatch.delenv("ACADEMIC_AI_BASE_URL", raising=False)
    monkeypatch.delenv("ACADEMIC_AI_API_KEY", raising=False)
    monkeypatch.delenv("ACADEMIC_AI_MODEL", raising=False)
    monkeypatch.delenv("ACADEMIC_AI_ASSISTANT_ID", raising=False)

    status = get_academic_ai_status()

    assert status.configured is False
    assert status.mode == "stub_not_configured"
    assert status.role == "advisory_only"
    assert "cannot execute machine motion directly" in status.safety_rule


def test_academic_ai_recommendation_never_executes_motion():
    from core.ai.academic_ai_client import build_ai_recommendation

    payload = build_ai_recommendation("approach")

    assert payload["execution_allowed"] is False
    assert payload["risk"] == "high"
    assert payload["target_phase"] == "2.3"
    assert "operator confirmation" in " ".join(payload["recommendation"])


def test_web_operator_console_has_academic_ai_window():
    html = (WEB_ROOT / "index.html").read_text(encoding="utf-8")
    js = (WEB_ROOT / "app.js").read_text(encoding="utf-8")

    assert "Academic AI Assistant" in html
    assert "id=\"ai-window\"" in html
    assert "id=\"ai-status\"" in html
    assert "/api/ai/status" in js
    assert "/api/ai/recommendation" in js

def test_web_operator_console_hidden_overlay_rule_exists():
    css = (WEB_ROOT / "style.css").read_text(encoding="utf-8")
    html = (WEB_ROOT / "index.html").read_text(encoding="utf-8")

    assert "[hidden]" in css
    assert "display: none !important" in css
    assert 'id="window-layer" hidden' in html


def test_web_operator_console_window_layer_is_not_visible_by_default():
    html = (WEB_ROOT / "index.html").read_text(encoding="utf-8")

    assert 'class="window-layer" id="window-layer" hidden' in html
    assert 'id="scan-window" hidden' in html
    assert 'id="live-window" hidden' in html
    assert 'id="ai-window" hidden' in html
