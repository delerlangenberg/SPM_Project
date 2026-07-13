from pathlib import Path

from core.web.operator_console_server import PHASE_MAP, WEB_ROOT, json_response


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_web_operator_console_files_exist():
    assert (WEB_ROOT / "index.html").exists()
    assert (WEB_ROOT / "style.css").exists()
    assert (WEB_ROOT / "app.js").exists()
    assert (WEB_ROOT / "window_manager.js").exists()
    assert (WEB_ROOT / "scan_raster.js").exists()


def test_phase_map_labels_future_integration_work():
    phases = {item["phase"]: item for item in PHASE_MAP}

    assert phases["2.0"]["status"] == "implemented"
    assert "System power" in phases["2.1"]["name"]
    assert "Z scanner" in phases["2.2"]["name"]
    assert "XY scanner" in phases["2.3"]["name"]
    assert "Live scan" in phases["2.4"]["name"]
    assert "operator workflow" in phases["2.5"]["name"]


def test_json_response_serializes_api_payload():
    payload = {"status": "ok", "phase": "2.3B"}
    body = json_response(payload)

    assert b'"status": "ok"' in body
    assert b'"phase": "2.3B"' in body


def test_web_operator_console_main_page_is_not_roadmap_page():
    html = (WEB_ROOT / "index.html").read_text(encoding="utf-8")

    assert "phase-roadmap" not in html
    assert "Integration Roadmap" not in html
    assert "id=\"phase-map\"" not in html


def test_web_operator_console_has_dropdown_menus():
    html = (WEB_ROOT / "index.html").read_text(encoding="utf-8")

    required = [
        "View",
        "Tools",
        "Open",
        "About",
        "Line Mode",
        "Topography",
        "Live View",
        "Scan Setup",
        "Academic AI Assistant",
    ]

    for marker in required:
        assert marker in html


def test_web_operator_console_uses_non_blocking_windows():
    html = (WEB_ROOT / "index.html").read_text(encoding="utf-8")
    css = (WEB_ROOT / "style.css").read_text(encoding="utf-8")
    window_js = (WEB_ROOT / "window_manager.js").read_text(encoding="utf-8")

    assert "window_manager.js" in html
    assert "window-layer" in html
    assert ".window-layer" in css
    assert "display: none" in css
    assert "SPMWindows" in window_js
    assert "closeAll" in window_js


def test_web_operator_console_main_page_keeps_essential_controls():
    html = (WEB_ROOT / "index.html").read_text(encoding="utf-8")

    required = [
        "Main System",
        "Z Scanner",
        "XY Jog Control",
        "Measurement Control",
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
        "Default Center",
        "Start Scanning",
        "Pause",
        "Stop",
    ]

    for marker in required:
        assert marker in html


def test_web_operator_console_has_directional_line_and_topography_windows():
    html = (WEB_ROOT / "index.html").read_text(encoding="utf-8")

    required = [
        "Line Mode - Directional Line Scans",
        "Topography - Directional Accumulation",
        "line-x-plus-canvas",
        "line-x-minus-canvas",
        "line-y-plus-canvas",
        "line-y-minus-canvas",
        "topography-x-plus-canvas",
        "topography-x-minus-canvas",
        "topography-y-plus-canvas",
        "topography-y-minus-canvas",
    ]

    for marker in required:
        assert marker in html


def test_web_operator_console_has_academic_ai_window():
    html = (WEB_ROOT / "index.html").read_text(encoding="utf-8")
    app_js = (WEB_ROOT / "app.js").read_text(encoding="utf-8")

    assert "Academic AI Assistant" in html
    assert "id=\"ai-window\"" in html
    assert "id=\"ai-status\"" in html
    assert "/api/ai/status" in app_js
    assert "/api/ai/recommendation" in app_js


def test_web_operator_console_uses_modular_raster_js():
    html = (WEB_ROOT / "index.html").read_text(encoding="utf-8")
    app_js = (WEB_ROOT / "app.js").read_text(encoding="utf-8")
    raster_js = (WEB_ROOT / "scan_raster.js").read_text(encoding="utf-8")

    assert "scan_raster.js" in html
    assert "window.SPMRaster" in raster_js
    assert "runRasterSimulation" in raster_js
    assert "stepOneLine" in raster_js
    assert "/api/scan/line" in raster_js
    assert "function runRasterSimulation" not in app_js


def test_academic_ai_advisory_status_is_safe_by_default(monkeypatch):
    from core.ai.academic_ai_client import get_academic_ai_status

    monkeypatch.delenv("ACADEMIC_AI_BASE_URL", raising=False)
    monkeypatch.delenv("ACADEMIC_AI_API_KEY", raising=False)
    monkeypatch.delenv("ACADEMIC_AI_MODEL", raising=False)
    monkeypatch.delenv("ACADEMIC_AI_ASSISTANT_ID", raising=False)
    monkeypatch.setenv("ACADEMIC_AI_DISABLE_LOCAL_FILE", "1")

    status = get_academic_ai_status()

    assert status.configured is False
    assert status.mode == "stub_not_configured"
    assert status.role == "advisory_only"
    assert "cannot execute machine motion directly" in status.safety_rule


def test_academic_ai_recommendation_never_executes_motion(monkeypatch):
    from core.ai.academic_ai_client import build_ai_recommendation

    monkeypatch.setenv("ACADEMIC_AI_DISABLE_LOCAL_FILE", "1")
    payload = build_ai_recommendation("approach")

    assert payload["execution_allowed"] is False
    assert payload["risk"] == "high"
    assert "operator confirmation" in " ".join(payload["recommendation"])


def test_spm_scan_simulation_line_model():
    from core.web.spm_scan_simulation import WebScanProfile, build_scan_line

    profile = WebScanProfile(x_points=8, y_points=4, z_setpoint=0.2)
    line = build_scan_line(profile, line_index=0)

    assert line["line_index"] == 0
    assert line["line_count"] == 4
    assert line["x_points"] == 8
    assert line["z_setpoint"] == 0.2
    assert line["height_source"] == "simulated_z_feedback_minus_setpoint"
    assert len(line["points"]) == 8
    assert "z_feedback" in line["points"][0]
    assert "surface_height" in line["points"][0]


def test_spm_scan_simulation_serpentine_direction():
    from core.web.spm_scan_simulation import WebScanProfile, build_scan_line

    profile = WebScanProfile(x_min=0, x_max=10, x_points=3, y_points=3, serpentine=True)
    forward = build_scan_line(profile, line_index=0)
    reverse = build_scan_line(profile, line_index=1)

    assert forward["direction"] == "X+"
    assert reverse["direction"] == "X-"
    assert forward["points"][0]["x"] == 0
    assert reverse["points"][0]["x"] == 10


def test_spm_scan_simulation_supports_bravais_lattice_surface():
    from core.web.spm_scan_simulation import WebScanProfile, build_scan_line

    profile = WebScanProfile(
        x_min=0,
        x_max=20,
        y_min=0,
        y_max=20,
        x_points=12,
        y_points=3,
        surface="bravais_lattice",
    )
    line = build_scan_line(profile, line_index=1)
    heights = [point["surface_height"] for point in line["points"]]

    assert line["x_points"] == 12
    assert max(heights) > min(heights)
    assert all(point["z_feedback"] >= profile.z_setpoint for point in line["points"])


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

def test_web_operator_console_supports_new_tab_views():
    html = (WEB_ROOT / "index.html").read_text(encoding="utf-8")
    window_js = (WEB_ROOT / "window_manager.js").read_text(encoding="utf-8")
    css = (WEB_ROOT / "style.css").read_text(encoding="utf-8")

    assert 'data-open-tab="line-window"' in html
    assert 'data-open-tab="topography-window"' in html
    assert 'data-open-tab="live-window"' in html
    assert "openTab" in window_js
    assert "standalone-window-mode" in window_js
    assert "standalone-window-mode" in css


def test_web_operator_console_dropdowns_are_click_stable():
    css = (WEB_ROOT / "style.css").read_text(encoding="utf-8")
    window_js = (WEB_ROOT / "window_manager.js").read_text(encoding="utf-8")

    assert ".menu-group.open .dropdown" in css
    assert "menuButton" in window_js
    assert "closeMenus" in window_js


def test_web_operator_console_measurement_workflow_requires_center_and_approach():
    html = (WEB_ROOT / "index.html").read_text(encoding="utf-8")
    raster_js = (WEB_ROOT / "scan_raster.js").read_text(encoding="utf-8")

    assert 'id="center-status"' in html
    assert "centerReady" in raster_js
    assert "approachReady" in raster_js
    assert "blocked: center first" in raster_js
    assert "blocked: approach first" in raster_js
    assert "runToken" in raster_js
    assert "Raster loop interrupted" in raster_js

def test_web_operator_console_view_items_are_real_new_tab_links():
    html = (WEB_ROOT / "index.html").read_text(encoding="utf-8")
    window_js = (WEB_ROOT / "window_manager.js").read_text(encoding="utf-8")

    assert 'href="/?window=line-window&amp;standalone=1"' in html
    assert 'href="/?window=topography-window&amp;standalone=1"' in html
    assert 'href="/?window=live-window&amp;standalone=1"' in html
    assert 'target="_blank"' in html
    assert "window.open" not in window_js


def test_web_operator_console_open_menu_has_no_view_duplicates():
    html = (WEB_ROOT / "index.html").read_text(encoding="utf-8")

    open_start = html.index('<button class="menu-button" type="button">Open</button>')
    about_start = html.index('<button class="menu-button" type="button">About</button>')
    open_block = html[open_start:about_start]

    assert "Scan Setup" in open_block
    assert "Line Mode" not in open_block
    assert "Topography" not in open_block
    assert "Z Feedback Live View" not in open_block


def test_web_operator_console_live_view_is_z_only():
    html = (WEB_ROOT / "index.html").read_text(encoding="utf-8")

    live_start = html.index('id="live-window"')
    status_start = html.index('id="status-window"')
    live_block = html[live_start:status_start]

    assert "Z Feedback Live View" in live_block
    assert "z-live-canvas" in live_block
    assert "fixed-distance monitoring" in live_block
    assert "Current X+ line scan" not in live_block
    assert "Accumulated X+ topography" not in live_block


def test_web_operator_console_has_separate_z_live_module():
    html = (WEB_ROOT / "index.html").read_text(encoding="utf-8")
    z_js = (WEB_ROOT / "z_live.js").read_text(encoding="utf-8")

    assert "z_live.js" in html
    assert "window.SPMZLive" in z_js
    assert "Z feedback" in z_js

def test_system_control_defaults_to_dry_run(monkeypatch):
    from core.web.system_control import system_on, system_status

    monkeypatch.delenv("SPM_WEB_ALLOW_REAL_MOTION", raising=False)

    payload = system_on(mode="dry_run")
    status = system_status()

    assert payload["powered"] is True
    assert payload["mode"] == "dry_run"
    assert payload["safety"]["gcode_sent"] is False
    assert payload["safety"]["motion_allowed_this_phase"] is False
    assert status["real_motion_enabled"] is False


def test_system_control_blocks_hardware_mode_without_explicit_gate(monkeypatch):
    from core.web.system_control import system_on

    monkeypatch.delenv("SPM_WEB_ALLOW_REAL_MOTION", raising=False)

    payload = system_on(mode="hardware")

    assert payload["status"] == "blocked"
    assert payload["powered"] is False
    assert payload["safety"]["gcode_sent"] is False
    assert "blocked" in payload["message"].lower()


def test_system_control_dry_run_plan_is_read_only():
    from core.web.system_control import dry_run_startup_plan

    payload = dry_run_startup_plan()
    plan = " ".join(payload["plan"])

    assert payload["execution_allowed"] is False
    assert payload["gcode_sent"] is False
    assert "M115" in plan
    assert "M119" in plan
    assert "M105" in plan
    assert "M114" in plan
    assert "G1" not in plan
    assert "G28" not in plan


def test_web_operator_console_calls_system_control_api():
    app_js = (WEB_ROOT / "app.js").read_text(encoding="utf-8")
    server_py = (PROJECT_ROOT / "core" / "web" / "operator_console_server.py").read_text(encoding="utf-8")

    assert "/api/system/on?mode=dry_run" in app_js
    assert "/api/system/off" in app_js
    assert "/api/system/status" in app_js
    assert "/api/system/close" in app_js
    assert 'route == "/api/system/status"' in server_py
    assert 'route == "/api/system/on"' in server_py
    assert 'route == "/api/system/dry-run"' in server_py

def test_hardware_status_adapter_uses_existing_information_layer():
    from core.web.hardware_status_adapter import hardware_information_status, validate_readonly_plan

    payload = hardware_information_status()

    assert payload["source_module"] == "core.system.hardware_information_exchange"
    assert payload["mode"] == "dry_run_readonly_plan"
    assert payload["execution_allowed"] is False
    assert payload["gcode_sent"] is False
    assert payload["readonly_actions"]["IDENTITY"] == "M115"
    assert payload["readonly_actions"]["TEMPERATURE"] == "M105"
    assert payload["readonly_actions"]["ENDSTOPS"] == "M119"
    assert payload["readonly_actions"]["POSITION"] == "M114"
    assert validate_readonly_plan(payload) is True


def test_system_status_contains_simulation_and_hardware_information_paths():
    from core.web.system_control import system_status

    payload = system_status()

    assert payload["simulation_status"]["available"] is True
    assert payload["simulation_status"]["mode"] == "web_simulation_dry_run"
    assert "hardware_information_status" in payload
    assert payload["hardware_information_status"]["mode"] == "dry_run_readonly_plan"
    assert payload["hardware_information_plan_valid"] is True
    assert payload["safety"]["serial_opened"] is False
    assert payload["safety"]["gcode_sent"] is False


def test_web_app_logs_hardware_information_layer():
    app_js = (WEB_ROOT / "app.js").read_text(encoding="utf-8")

    assert "Hardware information layer" in app_js
    assert "hardware_information_status" in app_js
    assert "command_plan" in app_js

def test_system_status_does_not_open_status_window():
    app_js = (WEB_ROOT / "app.js").read_text(encoding="utf-8")

    status_block_start = app_js.index('if (action === "system-status")')
    status_block_end = app_js.index('if (action === "system-on")')
    status_block = app_js[status_block_start:status_block_end]

    assert "/api/system/status" in status_block
    assert 'SPMWindows.open("status-window")' not in status_block


def test_visible_ai_ui_is_postponed_from_menu():
    html = (WEB_ROOT / "index.html").read_text(encoding="utf-8")
    app_js = (WEB_ROOT / "app.js").read_text(encoding="utf-8")

    nav_start = html.index('<nav class="menu-bar"')
    nav_end = html.index('</nav>', nav_start)
    nav = html[nav_start:nav_end]

    assert "Academic AI Assistant" not in nav
    assert "postponed" in html
    assert "AI advisory is postponed to a later dedicated phase" in app_js
    assert "loadAIStatus();" not in app_js


def test_view_menu_has_measurement_views_only_no_status_duplicate():
    html = (WEB_ROOT / "index.html").read_text(encoding="utf-8")

    view_start = html.index('<button class="menu-button" type="button">View</button>')
    tools_start = html.index('<button class="menu-button" type="button">Tools</button>')
    view_block = html[view_start:tools_start]

    assert "Line Mode" in view_block
    assert "Topography" in view_block
    assert "Z Feedback Live View" in view_block
    assert "System Status" not in view_block
    assert "Academic AI" not in view_block

def test_system_mode_selector_exists_and_uses_dry_run_default():
    html = (WEB_ROOT / "index.html").read_text(encoding="utf-8")
    app_js = (WEB_ROOT / "app.js").read_text(encoding="utf-8")

    assert 'id="system-mode"' in html
    assert 'value="dry_run"' in html
    assert 'value="hardware_readonly"' in html
    assert "selectedSystemMode" in app_js
    assert "encodeURIComponent(selectedSystemMode())" in app_js


def test_hardware_readonly_mode_is_locked_by_default(monkeypatch):
    from core.web.system_control import system_on

    monkeypatch.delenv("SPM_WEB_ALLOW_READONLY_HARDWARE", raising=False)
    payload = system_on(mode="hardware_readonly")

    assert payload["status"] == "blocked"
    assert payload["powered"] is False
    assert payload["mode"] == "hardware_readonly_locked"
    assert payload["safety"]["serial_opened"] is False
    assert payload["safety"]["gcode_sent"] is False


def test_hardware_motion_mode_remains_blocked():
    from core.web.system_control import system_on

    payload = system_on(mode="hardware_motion")

    assert payload["status"] == "blocked"
    assert payload["powered"] is False
    assert payload["safety"]["motion_allowed_this_phase"] is False
    assert payload["safety"]["gcode_sent"] is False


def test_off_and_close_clear_startup_plan_noise():
    from core.web.system_control import system_on, system_off, system_close

    system_on(mode="dry_run")
    off_payload = system_off()
    close_payload = system_close()

    assert off_payload["dry_run_plan"] == []
    assert close_payload["dry_run_plan"] == []


def test_app_does_not_log_startup_plan_for_off_close():
    app_js = (WEB_ROOT / "app.js").read_text(encoding="utf-8")

    assert 'label !== "System OFF"' in app_js
    assert 'label !== "System CLOSE"' in app_js


def test_web_z_scanner_control_routes_are_exposed():
    server_py = (PROJECT_ROOT / "core" / "web" / "operator_console_server.py").read_text(encoding="utf-8")
    z_js = (WEB_ROOT / "phase_2_2c4_safe_layout.js").read_text(encoding="utf-8")

    assert '"/api/z/read"' in server_py
    assert '"/api/z/auto-approach"' in server_py
    assert '"/api/z/move-to-setpoint"' in server_py
    assert "setpoint_distance_mm" in server_py
    assert '"/api/z/manual-step"' in server_py
    assert '"/api/z/retract"' in server_py
    assert '"/api/z/stop"' in server_py
    assert '"/api/measurement/limits"' in server_py
    assert "z-mini-live-canvas" in z_js
    assert "Apply Target Z" in z_js
    assert 'ev.key === "Enter"' in z_js
    assert "spm-apply-row" in z_js
    assert "spm-z-scale-bar" in z_js
    assert "spmZViewMode" in z_js
    assert "Retract target mm" not in z_js
    assert "Auto Approach" in z_js
    assert "data-z-stop" in z_js
    assert "STOP" in z_js


def test_main_workspace_has_inline_signal_windows_and_log_drawer():
    z_js = (WEB_ROOT / "phase_2_2c4_safe_layout.js").read_text(encoding="utf-8")
    css = (WEB_ROOT / "phase_2_2c4_safe_layout.css").read_text(encoding="utf-8")
    raster_js = (WEB_ROOT / "scan_raster.js").read_text(encoding="utf-8")
    html = (WEB_ROOT / "index.html").read_text(encoding="utf-8")
    log_js = (WEB_ROOT / "reliable_live_log.js").read_text(encoding="utf-8")

    assert "spm-inline-signal-panel" in z_js
    assert "Line Signal / Z Feedback" in z_js
    assert "spm-topography-x-plus-panel" in z_js
    assert "spm-topography-x-minus-panel" in z_js
    assert "live-line-canvas" in z_js
    assert "live-topography-x-plus-canvas" in z_js
    assert "live-topography-x-minus-canvas" in z_js
    assert "spm-log-drawer" in z_js
    assert "spmReliableLogOpenTab" in z_js
    assert "grid-area: signal" in css
    assert "grid-area: topo-plus" in css
    assert "grid-area: topo-minus" in css
    assert "spm-log-expanded" in css
    assert "live-topography-x-plus-canvas" in raster_js
    assert "live-topography-x-minus-canvas" in raster_js
    assert "/?window=log-window&standalone=1" in log_js
    assert "spmLiveLogSnapshot" in log_js
    assert 'id="log-window"' in html
    assert "resizable-layout-20260619" in html


def test_main_workspace_cards_are_movable_and_persistent():
    z_js = (WEB_ROOT / "phase_2_2c4_safe_layout.js").read_text(encoding="utf-8")
    css = (WEB_ROOT / "phase_2_2c4_safe_layout.css").read_text(encoding="utf-8")

    assert "installMovableCards" in z_js
    assert "spmOperatorCardLayoutV1" in z_js
    assert "Reset Card Layout" in z_js
    assert "pointerdown" in z_js
    assert "wireGlobalCardMoveHandlers" in z_js
    assert "finishCardMove" in z_js
    assert "spm-movable-card" in css
    assert "spm-drop-target" in css
    assert "spm-card-moving" in css


def test_main_workspace_cards_are_equal_height_and_resizable():
    z_js = (WEB_ROOT / "phase_2_2c4_safe_layout.js").read_text(encoding="utf-8")
    css = (WEB_ROOT / "phase_2_2c4_safe_layout.css").read_text(encoding="utf-8")

    assert "installResizableCards" in z_js
    assert "spmOperatorCardHeightsV1" in z_js
    assert "Reset Card Heights" in z_js
    assert "Start Scanning" in z_js
    assert ".main-panel" in css
    assert ".z-panel" in css
    assert ".measurement-panel" in css
    assert "height: 740px" in css
    assert "resize: vertical" in css


def test_z_auto_approach_web_facade_is_motion_locked_by_default(monkeypatch):
    from core.web.z_scanner_control import z_auto_approach

    monkeypatch.delenv("SPM_WEB_ALLOW_Z_MOTION", raising=False)

    payload = z_auto_approach(setpoint_distance_mm=1.0, retract_after=False, confirmed=True)

    assert payload["ok"] is False
    assert payload["status"] == "motion_locked"
    assert payload["commands"]


def test_z_move_to_setpoint_web_facade_is_motion_locked_by_default(monkeypatch):
    from core.web.z_scanner_control import z_move_to_setpoint

    monkeypatch.delenv("SPM_WEB_ALLOW_Z_MOTION", raising=False)

    payload = z_move_to_setpoint(target_z_mm=57.0, confirmed=True)

    assert payload["ok"] is False
    assert payload["status"] == "motion_locked"
    assert payload["target_z"] == 57.0


def test_z_stop_sets_software_stop_without_firmware_quick_stop(monkeypatch):
    from core.web.z_scanner_control import z_stop_now

    monkeypatch.delenv("SPM_WEB_ALLOW_Z_MOTION", raising=False)

    payload = z_stop_now()

    assert payload["ok"] is True
    assert payload["status"] == "stop_requested"
    assert "Software stop flag set" in payload["log_lines"][0]


def test_measurement_limits_payload_exposes_axis_limits_and_steps():
    from core.web.z_scanner_control import measurement_limits_payload

    payload = measurement_limits_payload()

    assert payload["ok"] is True
    assert payload["limits"]["x_min"] == -1.0
    assert payload["limits"]["x_max"] == 251.0
    assert payload["scanner"]["z_step_mm"] == 0.0025


def test_phase_2_1_visible_health_test_is_10_mm():
    health_py = (PROJECT_ROOT / "core" / "web" / "mk4s_health_motion.py").read_text(encoding="utf-8")
    main_js = (WEB_ROOT / "main_system_upgrade.js").read_text(encoding="utf-8")
    server_py = (PROJECT_ROOT / "core" / "web" / "operator_console_server.py").read_text(encoding="utf-8")

    assert "else 10.0" in health_py
    assert "X +/-10 mm" in main_js
    assert "spm-main-health-test-button" not in main_js
    assert "spm-main-long-health-test-button" not in main_js
    assert "diagnoseAndHealthTest" in main_js
    assert "XYZ axes" in main_js
    assert '"/api/system/diagnostics"' in server_py
    assert '"/api/system/sync-position"' in server_py
    assert "SYNC POSITION" in main_js
    assert "spm-main-hardware-state" in main_js
    assert '"/api/system/safe-standby"' in server_py
    assert "SAFE STANDBY" in main_js
    assert "X125 Y105 Z120" in main_js


def test_phase_2_1_position_diagnostic_detects_logical_count_mismatch():
    from core.web.system_control import _position_diagnostic

    diagnostic = _position_diagnostic("X:227.50 Y:105.00 Z:120.00 E:0 Count X:12500 Y:10500 Z:48000")

    assert diagnostic["ok"] is False
    assert diagnostic["status"] == "needs_sync"
    assert diagnostic["values"]["physical_x"] == 125.0
    assert diagnostic["mismatches"]
