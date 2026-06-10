from pathlib import Path


def test_gui_contains_z_dry_run_limit_validation():
    text = Path("core/application/gui_scan_launcher.py").read_text(encoding="utf-8")

    assert "self.limits.z_min <= z_position <= self.limits.z_max" in text
    assert "outside safe limits" in text
    assert "Invalid Z test value" in text
    assert "self.refresh_z_driver_status" in text


def test_gui_contains_z_dry_run_approach_retract_controls():
    text = Path("core/application/gui_scan_launcher.py").read_text(encoding="utf-8")

    assert "Z Dry Run: Approach" in text
    assert "Z Dry Run: Retract" in text
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
    assert "Z Connection" in text
    assert "Z Move Test" in text
    assert "Z Approach" in text
    assert "Z Retract" in text

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
    assert "Confirm GUI close" in text
    assert "Close the SPM workstation GUI" in text
    assert "The Z dry-run controller is still connected" in text
    assert "Recommended action: disconnect Z before closing" in text
    assert "event.accept()" in text
    assert "event.ignore()" in text
    assert "Close cancelled by operator" in text
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


def test_gui_confirms_before_dry_run_scan_command():
    source = Path("core/application/gui_scan_launcher.py").read_text(encoding="utf-8")

    confirmation_index = source.index('self.confirm_critical_action("Confirm dry-run scan"')
    command_index = source.index("command = self.build_cli_command(profile, execute_hardware=False)")

    assert confirmation_index < command_index
    assert "[SCAN] Dry-run scan cancelled by operator" in source

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
    assert "2 Scan Execution: Validate + Dry Run" in source
    assert "Z Scanner / Height Control" in source
    assert "1 Hardware / Power / Connection" in source
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

    scan_execution_start = source.index('scan_execution_group = QGroupBox("2 Scan Execution: Validate + Dry Run")')
    hardware_group_start = source.index('hardware_group = QGroupBox("1 Hardware / Power / Connection")')

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



