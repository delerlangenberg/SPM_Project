from pathlib import Path

from core.web.spm_scan_simulation import WebScanProfile, build_scan_line


APP_PATH = Path("core/application/operator_workstation_software.py")
APP_SOURCE = APP_PATH.read_text(encoding="utf-8")


def test_operator_workstation_uses_pyqt6():
    assert "from PyQt6.QtCore" in APP_SOURCE
    assert "from PyQt6.QtWidgets" in APP_SOURCE
    assert "PyQt5" not in APP_SOURCE


def test_operator_workstation_software_entrypoint_exists():
    assert APP_PATH.exists()
    assert "APP_VERSION = VERSION_STRING" in APP_SOURCE
    assert 'APP_TITLE = f"SPM Operator — {FULL_VERSION} ({BUILD_DATE_DISPLAY}) | Phase 2.1 Teaching Edition"' in APP_SOURCE
    assert "def main() -> int:" in APP_SOURCE
    assert "OperatorWorkstation()" in APP_SOURCE


def test_real_measurement_uses_dual_usb_commissioning_gate():
    assert "def real_measurement_blockers" in APP_SOURCE
    assert "discover_spm_ports()" in APP_SOURCE
    assert "evaluate_spm_readiness(port_map, mega_info)" in APP_SOURCE
    assert "Real Measurement Not Ready" in APP_SOURCE


def test_operator_workstation_has_standard_software_menu():
    assert "def build_menu_bar" in APP_SOURCE
    assert "menu.addMenu(\"File\")" in APP_SOURCE
    assert "menu.addMenu(\"View\")" in APP_SOURCE
    assert "menu.addMenu(\"Tools\")" in APP_SOURCE
    assert "menu.addMenu(\"About\")" in APP_SOURCE


def test_operator_workstation_has_visible_local_handbook_action():
    assert 'QPushButton("📖  Project Handbook")' in APP_SOURCE
    assert "def open_project_handbook" in APP_SOURCE
    assert '"OPEN_HANDBOOK.ps1"' in APP_SOURCE
    assert '"index.html"' in APP_SOURCE


def test_crtouch_prep_has_read_only_mega_functionality_test():
    assert '"Test Mega Connection — Read Only"' in APP_SOURCE
    assert "def test_mega_probe_connection" in APP_SOURCE
    assert "MegaProbeSerialTransport" in APP_SOURCE
    assert "discover_mega_candidate_ports" in APP_SOURCE
    assert "Download Live Log" in APP_SOURCE
    assert "Clear Live Log" in APP_SOURCE
    assert "Z Scanner" in APP_SOURCE
    assert "Live Log" in APP_SOURCE
    assert "Local AI Print File Export" in APP_SOURCE
    assert "CR Touch Probe Prep" in APP_SOURCE
    assert "Line Mode X+" in APP_SOURCE
    assert "Topography X+" in APP_SOURCE
    assert "class AcademicGCodeWindow(ToolWindow)" in APP_SOURCE
    assert "class CRTouchPrepWindow(ToolWindow)" in APP_SOURCE


def test_operator_workstation_has_phase_2_1_and_2_2_panels():
    assert "Device Connection & Preparation" in APP_SOURCE
    assert "SPM Operator — {FULL_VERSION} ({BUILD_DATE_DISPLAY}) | Phase 2.1 Teaching Edition" in APP_SOURCE
    assert "LAUNCH SCAN WORKSPACE" in APP_SOURCE
    assert "Applied Scan Parameters" in APP_SOURCE
    assert "Edit Parameters…" not in APP_SOURCE
    assert "QTabWidget" in APP_SOURCE
    assert "Profile:" in APP_SOURCE
    assert "button.setMinimumHeight(38)" in APP_SOURCE
    assert "self.system_state.setMinimumHeight(170)" in APP_SOURCE
    assert "class ZScannerWindow(ToolWindow)" in APP_SOURCE
    assert 'QGroupBox("Z Scanner")' in APP_SOURCE
    assert "QPushButton(\"Connect Hardware\")" in APP_SOURCE
    assert "AI Connection Assistant" in APP_SOURCE
    assert "Connecting..." in APP_SOURCE
    assert "Connected" in APP_SOURCE
    assert "YELLOW_BUTTON_STYLE" in APP_SOURCE
    assert "DISABLED_BUTTON_STYLE" in APP_SOURCE
    assert "update_system_connection_controls" in APP_SOURCE
    assert "self.system_connected" in APP_SOURCE
    assert "self.connect_button.setStyleSheet(GREEN_BUTTON_STYLE)" in APP_SOURCE
    assert "self.connect_button.setStyleSheet(YELLOW_BUTTON_STYLE)" in APP_SOURCE
    assert "self.disconnect_button.setEnabled(False)" in APP_SOURCE
    assert "Disconnect" in APP_SOURCE
    assert "Diagnosis" in APP_SOURCE
    assert "AI Error Correction" in APP_SOURCE
    assert "Safe Standby X125 Y105 Z120" in APP_SOURCE
    assert "Close Safely" in APP_SOURCE
    assert "GRAY_BUTTON_STYLE" in APP_SOURCE
    assert "diagnosis.setStyleSheet(GRAY_BUTTON_STYLE)" in APP_SOURCE
    assert "ai_fix.setStyleSheet(GRAY_BUTTON_STYLE)" in APP_SOURCE
    assert "standby.setStyleSheet(GRAY_BUTTON_STYLE)" in APP_SOURCE
    assert "close_button.setStyleSheet(GRAY_BUTTON_STYLE)" in APP_SOURCE
    assert "Connection activity" in APP_SOURCE
    assert "self.system_log" in APP_SOURCE
    assert "append_system_message" in APP_SOURCE
    assert "Manual Approach to Setpoint" in APP_SOURCE
    assert "Approach Advisor" in APP_SOURCE
    assert "current_approach_advice" in APP_SOURCE
    assert "run_approach_advisor" in APP_SOURCE
    assert "Approach Advisor Blocked Scan" in APP_SOURCE
    assert "advise_approach" in APP_SOURCE
    assert "Auto Approach" in APP_SOURCE
    assert "Retract Z" in APP_SOURCE
    assert "STOP Z" in APP_SOURCE
    assert "Auto Approach Simulation" in APP_SOURCE
    assert "Real sensor-based approach is disabled" in APP_SOURCE


def test_operator_workstation_live_z_trace_reacts_to_each_point():
    assert "class ZTraceWidget(QWidget)" in APP_SOURCE
    assert "def add_sample" in APP_SOURCE
    assert "pyqtSignal(dict)" in APP_SOURCE
    assert "on_sample=lambda sample: self.sample.emit(dict(sample))" in APP_SOURCE
    assert "[Z POINT]" in APP_SOURCE


def test_operator_workstation_has_adjustable_z_scale_modes():
    assert "Full" in APP_SOURCE
    assert "Auto" in APP_SOURCE
    assert "Zoom" in APP_SOURCE
    assert "set_zoom_window" in APP_SOURCE
    assert "Z_VIEW_FULL_RANGE = (0.0, 220.0)" in APP_SOURCE
    assert "\"Z mm\"" in APP_SOURCE


def test_operator_workstation_has_log_clear_and_download_controls():
    assert "def clear_log" in APP_SOURCE
    assert "def download_log" in APP_SOURCE
    assert "QFileDialog.getSaveFileName" in APP_SOURCE
    assert "spm_operator_software_" in APP_SOURCE


def test_operator_workstation_has_measurement_window_and_parameters():
    assert "class MeasurementWindow(ToolWindow)" in APP_SOURCE
    assert 'self.setWindowTitle("Scan Parameter Editor")' in APP_SOURCE
    assert "Tapping mode" in APP_SOURCE
    assert "Constant-height mode" in APP_SOURCE
    assert "Resolution [min:" in APP_SOURCE
    assert "Rotation [min:" in APP_SOURCE
    assert "Reset to 0°" in APP_SOURCE
    assert "Probe offset:" in APP_SOURCE
    assert "validate_scan_rectangle" in APP_SOURCE
    assert "Setpoint (Target) mm" in APP_SOURCE
    assert "Contact Limit (Safety Clamp) mm" in APP_SOURCE
    assert "Tapping range above setpoint mm" in APP_SOURCE
    assert "Expected surface Z mm" in APP_SOURCE
    assert "Coarse Approach Speed mm/s" in APP_SOURCE
    assert "Fine Approach Speed mm/s" in APP_SOURCE
    assert "Scan Speed [min: 1, max: 10] mm/s" in APP_SOURCE
    assert 'QPushButton("Apply")' in APP_SOURCE
    assert 'QPushButton("Start")' in APP_SOURCE
    assert 'QPushButton("Save")' in APP_SOURCE
    assert "GREEN_BUTTON_STYLE" in APP_SOURCE
    assert "RED_BUTTON_STYLE" in APP_SOURCE
    assert "bravais_lattice" in APP_SOURCE
    assert "teaching approximation" in APP_SOURCE


def test_operator_workstation_has_directional_line_and_topography_windows():
    assert "class SignalPlotWidget(QWidget)" in APP_SOURCE
    assert "open_signal_window" in APP_SOURCE
    assert "Line Mode Y-" in APP_SOURCE
    assert "Topography Y-" in APP_SOURCE
    assert "refresh_signal_windows" in APP_SOURCE
    assert "update_progress_views" in APP_SOURCE
    assert "Live Line Channel" in APP_SOURCE
    assert "Topography / Contrast Map" in APP_SOURCE
    assert "advance_measurement_point" in APP_SOURCE
    assert "build_virtual_scan_line" in APP_SOURCE
    assert "SimulationEngine" in APP_SOURCE
    assert "painter.drawEllipse" in APP_SOURCE
    assert "flat_signal" in APP_SOURCE


def test_operator_workstation_has_real_scan_worker_and_live_updates():
    assert "class RealScanWorker(QThread)" in APP_SOURCE
    assert "run_real_constant_z_scan" in APP_SOURCE
    assert "SPM_WEB_ALLOW_REAL_SCAN" in Path("core/web/real_scan_control.py").read_text(encoding="utf-8")
    assert "render_measurement_point" in APP_SOURCE
    assert "[REAL SCAN POINT]" in APP_SOURCE
    assert "request_real_scan_stop" in APP_SOURCE
    assert "request_real_scan_pause" in APP_SOURCE
    assert "clear_real_scan_pause" in APP_SOURCE


def test_operator_workstation_has_foil_tap_scan_mode():
    assert "FoilTapConfig" in APP_SOURCE
    assert "class FoilTapScanWorker(QThread)" in APP_SOURCE
    assert "run_real_foil_tap_scan" in APP_SOURCE
    assert "start_measurement_foil_tap_scan" in APP_SOURCE
    assert "Workpiece Zero (WZ)" in APP_SOURCE
    assert "Tapping range above setpoint mm" in APP_SOURCE
    assert "Z Search Window Cannot Reach Surface" in APP_SOURCE
    assert "The scanner would stop above the sample" in APP_SOURCE
    assert "Safe Park Height mm" in APP_SOURCE
    assert "approach_speed_mm_s" in APP_SOURCE
    assert "approach until contact -> record contact Z -> retract -> next point" in APP_SOURCE
    assert "experimental M119 z_min contact detection" in APP_SOURCE


def test_operator_workstation_closes_through_safe_standby_then_disconnect():
    assert "def closeEvent" in APP_SOURCE
    assert "def request_safe_exit" in APP_SOURCE
    assert "def begin_safe_shutdown" in APP_SOURCE
    assert "def _start_safe_shutdown_worker" in APP_SOURCE
    assert "exit_action.triggered.connect(self.request_safe_exit)" in APP_SOURCE
    assert "QProgressDialog" in APP_SOURCE
    assert "Safe shutdown in progress" in APP_SOURCE
    assert "system_safe_standby_for_close()" in APP_SOURCE
    assert "system_disconnect()" in APP_SOURCE
    assert "QTimer.singleShot(250, self._continue_safe_shutdown_when_idle)" in APP_SOURCE
    assert "[SAFE CLOSE]" in APP_SOURCE


def test_current_release_record_exists():
    release_record = Path("docs/RELEASE_v1.3.1.0.md")
    assert release_record.is_file()
    assert "Adaptive object discovery" in release_record.read_text(encoding="utf-8")


def test_operator_workstation_has_review_only_gcode_and_crtouch_tools():
    assert "GCodePatternRequest" in APP_SOURCE
    assert "build_academic_gcode_job" in APP_SOURCE
    assert "Local AI Print File Studio" in APP_SOURCE
    assert "What do you want to build?" in APP_SOURCE
    assert "1. Printer Parameters" in APP_SOURCE
    assert "2. AI Build Request" in APP_SOURCE
    assert "3. Interactive AI Discussion" in APP_SOURCE
    assert "QSplitter(Qt.Orientation.Vertical)" in APP_SOURCE
    assert "workspace.setChildrenCollapsible(False)" in APP_SOURCE
    assert "form = QGridLayout()" in APP_SOURCE
    assert "compact_controls" in APP_SOURCE
    assert "Size mm" in APP_SOURCE
    assert "Layer Z mm" in APP_SOURCE
    assert "Feed mm/min" in APP_SOURCE
    assert "self.chat_transcript.setMinimumHeight(260)" in APP_SOURCE
    assert "Learning Notes" in APP_SOURCE
    assert "Send to AI" in APP_SOURCE
    assert "Use AI Suggested Parameters" in APP_SOURCE
    assert "Confirm Final" in APP_SOURCE
    assert "Create Code" in APP_SOURCE
    assert "Save As" in APP_SOURCE
    assert "minimum_supported_discussion_rounds" in APP_SOURCE
    assert "self.chat_history" in APP_SOURCE
    assert "self.chat_turn_count" in APP_SOURCE
    assert "def send_ai_message" in APP_SOURCE
    assert "def apply_ai_suggested_parameters" in APP_SOURCE
    assert "Show Code" in APP_SOURCE
    assert "toggle_code_view" in APP_SOURCE
    assert "self.code_view.setVisible(False)" in APP_SOURCE
    assert "Save Learning Notes" in APP_SOURCE
    assert "academic_ai_print_learning_notes.txt" in APP_SOURCE
    assert "setPlaceholderText" in APP_SOURCE
    assert "Material" in APP_SOURCE
    assert "Nozzle mm" in APP_SOURCE
    assert "Nozzle C" in APP_SOURCE
    assert "Bed C" in APP_SOURCE
    assert "Layer Z mm" in APP_SOURCE
    assert "Spacing mm" in APP_SOURCE
    assert "Export" in APP_SOURCE
    assert "Import STL/3MF/STEP/OBJ/AMF" in APP_SOURCE
    assert "G-code Preview" in APP_SOURCE
    assert "PrusaSlicer can import" in APP_SOURCE
    assert "OBJ/STL" in APP_SOURCE
    assert "self.generate_button.setEnabled(False)" in APP_SOURCE
    assert "self.save_button.setEnabled(False)" in APP_SOURCE
    assert "gcode_sent=False" in APP_SOURCE
    assert "CRTouchProbePlan" in APP_SOURCE
    assert "Test Mega Connection — Read Only" in APP_SOURCE
    assert "Read MK4S Status M119" in APP_SOURCE
    assert "integration_checklist" in APP_SOURCE


def test_scan_profile_supports_four_primary_directions():
    x_plus = build_scan_line(WebScanProfile(x_min=0, x_max=10, y_min=0, y_max=20, x_points=3, y_points=3, scan_direction="X+"), 0)
    x_minus = build_scan_line(WebScanProfile(x_min=0, x_max=10, y_min=0, y_max=20, x_points=3, y_points=3, scan_direction="X-"), 0)
    y_plus = build_scan_line(WebScanProfile(x_min=0, x_max=10, y_min=0, y_max=20, x_points=3, y_points=3, scan_direction="Y+"), 0)
    y_minus = build_scan_line(WebScanProfile(x_min=0, x_max=10, y_min=0, y_max=20, x_points=3, y_points=3, scan_direction="Y-"), 0)

    assert [point["x"] for point in x_plus["points"]] == [0, 5, 10]
    assert [point["x"] for point in x_minus["points"]] == [10, 5, 0]
    assert [point["y"] for point in y_plus["points"]] == [0, 10, 20]
    assert [point["y"] for point in y_minus["points"]] == [20, 10, 0]


def test_two_object_repeat_scan_is_integrated_behind_real_hardware_gates():
    assert "Discover & Refine Objects" in APP_SOURCE
    assert "def start_two_object_adaptive_scan" in APP_SOURCE
    assert 'self.motion_authorization != "OPERATIONAL"' in APP_SOURCE
    assert "real_measurement_blockers()" in APP_SOURCE
    assert "Authorize and Start Real Scan" in APP_SOURCE
    assert "Raised-object search floor: Z{raised_floor:.2f} mm" in APP_SOURCE
    assert "Safe XY travel and final retract: Z{safe_z:.2f} mm" in APP_SOURCE
    assert "mount_profile_blockers(PROJECT_ROOT)" in APP_SOURCE


def test_two_object_repeat_scan_exposes_progress_and_evidence():
    assert "TwoObjectAdaptiveScanWorker" in APP_SOURCE
    assert "COARSE_OBJECTS" in APP_SOURCE
    assert "MAP (?:object|magnet)=" in APP_SOURCE
    assert "Open Result Plot" in APP_SOURCE
    assert "Open Handbook" in APP_SOURCE


def test_two_object_repeat_scan_offers_explicit_resolution_profiles():
    assert "Balanced · 20 mm overview → 5 mm focus" in APP_SOURCE
    assert "Precision · 20 mm overview → 2.5 mm focus" in APP_SOURCE
    assert "Research · 15 mm overview → 1 mm focus" in APP_SOURCE
    assert "run_verified_two_magnet_map(self.resolution)" in APP_SOURCE
