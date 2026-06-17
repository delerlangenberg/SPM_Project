from pathlib import Path


def test_gui_contains_z_dry_run_limit_validation():
    text = Path("core/application/gui_scan_launcher.py").read_text(encoding="utf-8")

    assert "self.limits.z_min <= z_position <= self.limits.z_max" in text
    assert "outside safe limits" in text
    assert "Invalid Z test value" in text
    assert "self.refresh_z_driver_status" in text


def test_gui_contains_z_dry_run_approach_retract_controls():
    text = Path("core/application/gui_scan_launcher.py").read_text(encoding="utf-8")

    assert "AUTO APPROACH DRY RUN" in text
    assert "RETRACT Z DRY RUN" in text
    assert "self.z_approach_start" in text
    assert "self.z_approach_target" in text
    assert "self.z_retract_start" in text
    assert "self.z_retract_target" in text
    assert "self.z_step_size" in text


def test_gui_contains_z_dry_run_approach_retract_safety_validation():
    text = Path("core/application/gui_scan_launcher.py").read_text(encoding="utf-8")

    assert "def run_z_dry_approach" in text
    assert "def run_z_dry_retract" in text
    assert "step_size <= 0" in text
    assert "self.limits.z_min <= start_z <= self.limits.z_max" in text
    assert "self.limits.z_min <= target_z <= self.limits.z_max" in text
    assert "Invalid approach direction" in text
    assert "Invalid retract direction" in text
    assert "self.z_driver.approach" in text
    assert "self.z_driver.retract" in text
    assert "self.refresh_z_driver_status" in text

def test_gui_contains_grouped_z_control_layout():
    text = Path("core/application/gui_scan_launcher.py").read_text(encoding="utf-8")

    assert "QGroupBox" in text
    assert "Z-control dry-run tools" in text
    assert "Approach Simulator Connection" in text
    assert "Manual Z Move Preview" in text
    assert "Auto Approach Preview" in text
    assert "Safe Retract Preview" in text

def test_gui_contains_z_driver_status_refresh_helper():
    text = Path("core/application/gui_scan_launcher.py").read_text(encoding="utf-8")

    assert "def refresh_z_driver_status" in text
    assert "self.z_driver.get_status()" in text
    assert "mode={status['mode']}" in text
    assert "connected={status['connected']}" in text
    assert "last_command={status['last_command']}" in text
    assert "[Z STATUS]" in text

def test_gui_contains_consistent_z_failure_helper():
    text = Path("core/application/gui_scan_launcher.py").read_text(encoding="utf-8")

    assert "def report_z_failure" in text
    assert "Z dry-run status: {status_text}" in text
    assert "[Z FAILURE]" in text
    assert "self.report_z_failure" in text
    assert "Invalid Z test value" in text
    assert "Invalid approach value" in text
    assert "Invalid retract value" in text
    assert "Invalid approach direction" in text
    assert "Invalid retract direction" in text

def test_gui_contains_workstation_style_z_connection_header():
    text = Path("core/application/gui_scan_launcher.py").read_text(encoding="utf-8")

    assert "QHBoxLayout" in text
    assert "self.z_connection_state_label" in text
    assert "def set_z_connection_indicator" in text
    assert "CONNECTED" in text
    assert "DRY RUN" in text
    assert "READY TO CONNECT" in text
    assert "CONNECT Z DRY RUN" in text
    assert "DISCONNECT Z" in text
    assert "background-color: #2e7d32" in text
    assert "background-color: #c62828" in text
    assert "z_connection_bar = QHBoxLayout()" in text

def test_gui_contains_professional_z_connection_button_states_and_confirmations():
    text = Path("core/application/gui_scan_launcher.py").read_text(encoding="utf-8")

    assert "QMessageBox" in text
    assert "def confirm_z_action" in text
    assert "Confirm Z disconnect" in text
    assert "Confirm Z approach" in text
    assert "Confirm Z retract" in text
    assert "READY TO CONNECT" in text
    assert "CONNECTED ? DRY RUN" in text
    assert "DISCONNECTED" in text
    assert "background-color: #757575" in text
    assert "Disconnect cancelled by operator" in text
    assert "Approach cancelled by operator" in text
    assert "Retract cancelled by operator" in text

def test_gui_contains_global_critical_action_confirmation_and_close_warning():
    text = Path("core/application/gui_scan_launcher.py").read_text(encoding="utf-8")

    assert "def confirm_critical_action" in text
    assert "def closeEvent" in text
    assert "Power off required" in text
    assert "Close is locked until POWER OFF / SAFE PARK completes" in text
    assert "def power_off_workstation" in text
    assert "Deinitialize Educational SPM and move to safe position" in text
    assert "disconnect dry-run Z" in text
    assert "Parking sequence: Z ->" in text
    assert "event.accept()" in text
    assert "event.ignore()" in text
    assert "Close blocked: power-off/safe-park required" in text
    assert "return self.confirm_critical_action(title, message)" in text


def test_gui_has_scan_confirmation_message_builder():
    source = Path("core/application/gui_scan_launcher.py").read_text(encoding="utf-8")

    assert "def build_scan_confirmation_message(" in source
    assert "Scan mode:" in source
    assert "Scan area:" in source
    assert "Z value:" in source
    assert "Resolution:" in source
    assert "Output file:" in source
    assert "Color map:" in source
    assert "Dry-run safety active" in source


def test_gui_confirms_before_demo_scan_command():
    source = Path("core/application/gui_scan_launcher.py").read_text(encoding="utf-8")

    confirmation_index = source.index('self.confirm_critical_action("Confirm demo scan"')
    command_index = source.index("command = self.build_cli_command(profile, execute_hardware=False)")

    assert confirmation_index < command_index
    assert "[SCAN] Demo scan cancelled by operator" in source

def test_scan_confirmation_uses_existing_output_file_widget():
    source = Path("core/application/gui_scan_launcher.py").read_text(encoding="utf-8")

    assert "self.output_file.text().strip()" in source
    assert "self.output_path" not in source

def test_hardware_scan_uses_global_critical_confirmation():
    source = Path("core/application/gui_scan_launcher.py").read_text(encoding="utf-8")

    hardware_method_index = source.index("def run_hardware_scan")
    hardware_method = source[hardware_method_index:]

    assert "QMessageBox.question(" not in hardware_method
    assert 'self.confirm_critical_action(' in hardware_method
    assert '"Confirm hardware scan"' in hardware_method
    assert "execute_hardware=True" in hardware_method
    assert "[HARDWARE] Hardware scan cancelled by operator" in hardware_method


def test_hardware_confirmation_has_real_motion_warning():
    source = Path("core/application/gui_scan_launcher.py").read_text(encoding="utf-8")

    assert "REAL HARDWARE EXECUTION REQUESTED" in source
    assert "XY hardware motion may occur" in source
    assert "scanner, sample area, toolhead, bed, and operator area are clear" in source
    assert "Dry-run safety active: no hardware movement will be executed." in source

def test_gui_has_workstation_layout_panels():
    source = Path("core/application/gui_scan_launcher.py").read_text(encoding="utf-8")

    assert "XY Scan Setup" in source
    assert "2 Scan Execution: Validate + Dry Run First" in source
    assert "MK4S Z Height / Approach Training" in source
    assert "Hardware Check / Power / Connection" in source
    assert "2 Safety / Hardware Arm State" in source
    assert "Live Data / Raster Plot Preview" in source
    assert "Operator Log" in source


def test_gui_separates_xy_scan_from_z_height_control():
    source = Path("core/application/gui_scan_launcher.py").read_text(encoding="utf-8")

    assert 'form_layout.addRow("Z:", self.z)' not in source
    assert 'z_height_layout.addRow("Scan Z height:", self.z)' in source
    assert "XY Scan Setup" in source
    assert "Z Height / Safe Position" in source


def test_gui_has_phase_6_1_placeholders():
    source = Path("core/application/gui_scan_launcher.py").read_text(encoding="utf-8")

    assert "SYSTEM STATUS: SAFE MODE / DRY-RUN DEFAULT" in source
    assert "Placeholder: COM port, baudrate, machine connection, hardware readiness, last known state." in source
    assert "Placeholder: safe scan limits, safe Z range, critical-action confirmations, warning state." in source
    assert "Placeholder for last generated PNG, future live raster image, and signal monitor." in source

def test_hardware_scan_button_is_in_hardware_panel_not_scan_execution():
    source = Path("core/application/gui_scan_launcher.py").read_text(encoding="utf-8")

    scan_execution_start = source.index('scan_execution_group = QGroupBox("2 Scan Execution: Validate + Dry Run First")')
    hardware_group_start = source.index('hardware_group = QGroupBox("Hardware Check / Power / Connection")')

    scan_execution_block = source[scan_execution_start:hardware_group_start]
    hardware_block = source[hardware_group_start:]

    assert "scan_execution_layout.addWidget(self.execute_btn)" not in scan_execution_block
    assert "hardware_layout.addWidget(self.execute_btn)" in hardware_block


def test_hardware_scan_button_is_visually_dangerous():
    source = Path("core/application/gui_scan_launcher.py").read_text(encoding="utf-8")

    assert 'QPushButton("REAL HARDWARE SCAN")' in source
    assert "background-color: #ef6c00" in source
    assert "color: white" in source


def test_hardware_arm_disarm_visual_state_logic_exists():
    source = Path("core/application/gui_scan_launcher.py").read_text(encoding="utf-8")

    assert 'self.hardware_armed = False' in source
    assert 'QPushButton("ENABLE REAL MOTION")' in source
    assert 'QPushButton("DISABLE REAL MOTION")' in source

    assert 'self.hardware_arm_btn.setEnabled(False)' in source
    assert 'self.hardware_arm_btn.setEnabled(True)' in source
    assert 'self.hardware_disarm_btn.setEnabled(True)' in source
    assert 'self.hardware_disarm_btn.setEnabled(False)' in source

    assert 'self.execute_btn.setEnabled(True)' in source
    assert 'self.execute_btn.setEnabled(False)' in source

    assert 'background-color: #2e7d32' in source
    assert 'background-color: #b71c1c' in source
    assert 'background-color: #ef6c00' in source
    assert 'background-color: #9e9e9e' in source


def test_hardware_scan_is_blocked_when_disarmed():
    source = Path("core/application/gui_scan_launcher.py").read_text(encoding="utf-8")

    hardware_scan_start = source.index("def run_hardware_scan")
    hardware_scan_block = source[hardware_scan_start:]

    assert "if not self.hardware_armed:" in hardware_scan_block
    assert "[SAFETY] Hardware scan blocked because hardware is DISARMED" in hardware_scan_block
    assert "return" in hardware_scan_block


def test_system_check_runs_no_motion_hardware_report_before_real_motion():
    source = Path("core/application/gui_scan_launcher.py").read_text(encoding="utf-8")

    system_check_start = source.index("def initiate_system_check")
    arm_start = source.index("def arm_hardware")
    system_check_block = source[system_check_start:arm_start]

    assert "run_hardware_communication_report(self.config)" in system_check_block
    assert "no-motion hardware communication report" in system_check_block
    assert "if not report.passed:" in system_check_block
    assert "SYSTEM CHECK FAILED - inspect hardware report" in system_check_block


def test_gui_embeds_generated_raster_plot_preview():
    source = Path("core/application/gui_scan_launcher.py").read_text(encoding="utf-8")

    assert "from PyQt5.QtGui import QPixmap" in source
    assert "def refresh_plot_preview" in source
    assert "self.plot_placeholder.setPixmap" in source
    assert "feedback_tabs.addTab(self.plot_placeholder, \"Raster Preview\")" in source
    assert "self.refresh_plot_preview(plot_path)" in source


def test_gui_has_scan_progress_indicator():
    source = Path("core/application/gui_scan_launcher.py").read_text(encoding="utf-8")

    assert "QProgressBar" in source
    assert "self.scan_progress_bar.setRange(0, 100)" in source
    assert "def set_scan_progress" in source
    assert "measurement_live_layout.addWidget(self.scan_progress_bar)" in source
    assert "demo scan starting" in source
    assert "hardware scan starting" in source


def test_gui_has_real_spm_workstation_tabs_and_style():
    source = Path("core/application/gui_scan_launcher.py").read_text(encoding="utf-8")

    assert "QTabWidget" in source
    assert "feedback_tabs.addTab(self.plot_placeholder, \"Raster Preview\")" in source
    assert "feedback_tabs.addTab(self.line_scan_placeholder, \"Line Scan\")" in source
    assert "feedback_tabs.addTab(self.topography_placeholder, \"Topography\")" in source
    assert "feedback_tabs.addTab(z_feedback_tab, \"Z / Probe\")" in source
    assert "def apply_instrument_style" in source
    assert "QProgressBar::chunk" in source


def test_gui_has_no_motion_mk4s_position_query_and_crtouch_plan():
    source = Path("core/application/gui_scan_launcher.py").read_text(encoding="utf-8")

    assert "CRTouchProbePlan" in source
    assert "READ MK4S POSITION" in source
    assert "def query_mk4s_position" in source
    assert "No-motion position query" in source
    assert "self.z_probe_plan_label" in source


def test_gui_exposes_spm_scan_mode_selector():
    source = Path("core/application/gui_scan_launcher.py").read_text(encoding="utf-8")

    assert "VALID_SCAN_MODES" in source
    assert "self.scan_mode_dropdown = QComboBox()" in source
    assert "form_layout.addRow(\"Scan mode:\", self.scan_mode_dropdown)" in source
    assert "def show_scan_mode_limits" in source
    assert "def apply_scan_mode_preset" in source
    assert "get_scan_mode_preset(self.config, mode)" in source
    assert "scan_mode_limits_text(mode)" in source
    assert "mode=self.scan_mode_dropdown.currentText()" in source


def test_gui_exposes_scan_timing_and_z_setup_controls():
    source = Path("core/application/gui_scan_launcher.py").read_text(encoding="utf-8")

    assert "self.xy_feedrate = QLineEdit" in source
    assert "self.z_feedrate = QLineEdit" in source
    assert "self.z_dwell_ms = QLineEdit" in source
    assert "def refresh_timing_estimate" in source
    assert "Line time:" in source
    assert "Frame time:" in source
    assert "MANUAL Z MOVE DRY RUN" in source
    assert "AUTO APPROACH DRY RUN" in source
    assert "def current_z_setup_summary" in source


def test_gui_presents_professional_educational_spm_operator_flow():
    source = Path("core/application/gui_scan_launcher.py").read_text(encoding="utf-8")

    assert "APP_VERSION" in source
    assert "APP_PHASE" in source
    assert "APP_TITLE" in source
    assert "self.setWindowTitle(APP_TITLE)" in source
    assert "ABOUT" in source
    assert "documentation_markdown" in source
    assert "For a 100 x 100 mm object" in source
    assert "Current MK4S position" in source
    assert "Current installed hardware: original Prusa MK4S X/Y/Z motion only" in source
    assert "def z_axis_visual" in source
    assert "Training visual only" in source
    assert "POWER OFF / SAFE PARK" in source


def test_gui_shows_axis_limits_and_resolution_tips_beside_inputs():
    source = Path("core/application/gui_scan_launcher.py").read_text(encoding="utf-8")

    assert "SPMHardwareProfile" in source
    assert "def field_with_tip" in source
    assert "self.hardware_profile.compact_axis_range(\"X\")" in source
    assert "self.hardware_profile.compact_axis_range(\"Y\")" in source
    assert "self.hardware_profile.compact_resolution_range()" in source
    assert "self.hardware_tuning_label" in source


def test_gui_updates_line_topography_and_z_feedback_from_scan_data():
    source = Path("core/application/gui_scan_launcher.py").read_text(encoding="utf-8")

    assert "frame.line_scan_summary()" in source
    assert "frame.topography_summary()" in source
    assert "frame.z_feedback_summary()" in source


def test_gui_locks_actions_until_initialization_passes():
    source = Path("core/application/gui_scan_launcher.py").read_text(encoding="utf-8")

    assert "def set_initialized_controls_enabled" in source
    assert "self.set_initialized_controls_enabled(False)" in source
    assert "def require_initialized" in source
    assert "Initialization required" in source
    assert "Profile validation" in source
    assert "Dry-run scan" in source
    assert "MK4S position query" in source
    assert "Park MK4S" in source
    assert "Z dry-run connect" in source
    assert "Hardware scan" in source


def test_initialization_popup_contains_safety_checklist():
    source = Path("core/application/gui_scan_launcher.py").read_text(encoding="utf-8")

    assert "Initialize SPM workstation" in source
    assert "Initialization is starting" in source
    assert "MK4S power is ON" in source
    assert "bed/surface area is clear" in source
    assert "no-motion hardware communication checks" in source
    assert "validate_profile(require_initialized=False)" in source


def test_gui_parks_mk4s_on_button_and_close():
    source = Path("core/application/gui_scan_launcher.py").read_text(encoding="utf-8")

    assert "from core.motion.parking import park_mk4s" in source
    assert 'self.park_btn = QPushButton("PARK MK4S")' in source
    assert 'self.power_off_btn = QPushButton("POWER OFF / SAFE PARK")' in source
    assert 'self.close_btn = QPushButton("CLOSE SOFTWARE")' in source
    assert "def park_workstation" in source
    assert "def power_off_workstation" in source
    assert "def close_after_power_off" in source
    assert "Sequence: Z ->" in source
    assert "park_mk4s(self.config)" in source
    assert "safe park complete" in source


def test_gui_has_documentation_tab_and_fixed_live_frames():
    source = Path("core/application/gui_scan_launcher.py").read_text(encoding="utf-8")

    assert "QTextBrowser" in source
    assert "QScrollArea" in source
    assert "workstation_scroll.setWidgetResizable(True)" in source
    assert "root_tabs.addTab(workstation_scroll, \"Workstation\")" in source
    assert "root_tabs.addTab(self.documentation_browser, \"Documentation\")" in source
    assert "setFixedSize(460, 260)" in source
    assert "setFixedSize(460, 145)" in source
    assert "setFixedSize(460, 220)" in source
    assert "MAX_SCAN_RESOLUTION" in source
    assert "OPEN SCAN VIEWER" in source
    assert "def open_scan_viewer" in source


def test_gui_uses_two_row_operator_console_for_monitor_fit():
    source = Path("core/application/gui_scan_launcher.py").read_text(encoding="utf-8")

    assert "session_row = QHBoxLayout()" in source
    assert "tools_row = QHBoxLayout()" in source
    assert "main_command_layout.addLayout(session_row)" in source
    assert "main_command_layout.addLayout(tools_row)" in source
    assert "available = screen.availableGeometry()" in source
    assert "self.resize(min(1040" in source


def test_gui_has_live_hardware_parameter_panel_and_shutdown_gate():
    source = Path("core/application/gui_scan_launcher.py").read_text(encoding="utf-8")

    assert "self.hardware_parameters_label" in source
    assert "def refresh_hardware_parameters" in source
    assert "Phase:" in source
    assert "Shutdown ready:" in source
    assert "self.shutdown_complete = False" in source
    assert "if not self.shutdown_complete:" in source
    assert "self.close_btn.setEnabled(True)" in source


def test_gui_has_power_top_level_and_measurement_windows():
    source = Path("core/application/gui_scan_launcher.py").read_text(encoding="utf-8")

    assert 'QPushButton("POWER ON / INITIALIZE")' in source
    assert 'QPushButton("POWER OFF / SAFE PARK")' in source
    assert 'QPushButton("CLOSE SOFTWARE")' in source
    assert 'QPushButton("MEASUREMENT SETUP")' in source
    assert 'QPushButton("XY SCANNER")' in source
    assert 'QPushButton("Z REGULATION")' in source
    assert 'QPushButton("HARDWARE CHECK")' in source
    assert 'QPushButton("RUN HARDWARE CHECK")' in source
    assert "def open_measurement_window" in source
    assert "def open_xy_scanner_window" in source
    assert "def open_z_regulation_window" in source
    assert "measurement_live_layout.addWidget(self.scan_progress_bar)" in source
    assert "measurement_live_layout.addWidget(feedback_tabs)" in source
    assert "def run_hardware_check_only" in source


def test_gui_has_matrix_style_direction_windows_and_version_about():
    source = Path("core/application/gui_scan_launcher.py").read_text(encoding="utf-8")

    assert '"FORWARD IMAGE"' in source
    assert '"BACKWARD IMAGE"' in source
    assert '"UPWARD IMAGE"' in source
    assert '"DOWNWARD IMAGE"' in source
    assert "def open_direction_window" in source
    assert "def direction_window_text" in source
    assert "self.direction_preview_labels" in source
    assert "self.direction_window_labels" in source
    assert "show_about" in source
    assert "Educational SPM {APP_VERSION}" in source


def test_gui_has_single_instance_guard():
    source = Path("core/application/gui_scan_launcher.py").read_text(encoding="utf-8")

    assert "def acquire_single_instance_socket" in source
    assert "127.0.0.1" in source
    assert "Educational SPM already running" in source
    assert "gui.instance_guard = instance_guard" in source



