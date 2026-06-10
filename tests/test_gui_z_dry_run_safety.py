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
