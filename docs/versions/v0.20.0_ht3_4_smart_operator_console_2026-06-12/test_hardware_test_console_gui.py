from pathlib import Path


def test_hardware_test_console_gui_exposes_all_hardware_test_buttons():
    source = Path("core/application/hardware_test_console_gui.py").read_text(encoding="utf-8")

    assert 'APP_VERSION = "v0.20.0"' in source
    assert "HT3.4 Smart Operator Console" in source
    assert "HardwareTestConsole" in source
    assert "Smart Operator Console" in source
    assert "Expert: Read-Only Hardware Information" in source
    assert "Expert: Supervised Hardware Test Controls" in source
    assert "Preview Selected Command" in source
    assert "EXECUTE SELECTED ON REAL HARDWARE" in source
    assert "READ_POSITION" in source
    assert "SAFE_RETRACT" in source
    assert "SAFE_CENTER" in source
    assert "X_STEP_PLUS" in source
    assert "Y_STEP_PLUS" in source
    assert "Z_STEP_DOWN" in source


def test_hardware_test_console_gui_real_motion_requires_supervised_gate():
    source = Path("core/application/hardware_test_console_gui.py").read_text(encoding="utf-8")

    assert "Enable supervised real motion" in source
    assert "type SUPERVISED" in source
    assert 'self.confirm_text.text().strip() == "SUPERVISED"' in source
    assert "REAL MOTION LOCKED" in source
    assert "[MOTION LOCKED]" in source
    assert "QMessageBox.information" in source
    assert "Confirm supervised real motion" in source
    assert "QMessageBox.warning" in source
    assert "execute=execute" in source
    assert '"PREVIEW"' in source


def test_hardware_test_console_gui_keeps_readonly_separate_from_motion():
    source = Path("core/application/hardware_test_console_gui.py").read_text(encoding="utf-8")

    assert "Show expert hardware controls" in source
    assert "Run real read-only exchange on COM5" in source
    assert "Run Real Connection Check" in source
    assert "Read Current XYZ - Real Safe" in source
    assert "run_real_information_exchange(action)" in source
    assert 'run_real_information_exchange("POSITION")' in source
    assert "run_hardware_test_action" in source
    assert "No motion commands are included." in source


def test_hardware_test_console_gui_allows_real_position_without_motion_unlock():
    source = Path("core/application/hardware_test_console_gui.py").read_text(encoding="utf-8")

    assert "def run_real_position_read" in source
    assert 'if execute and selected_action == "READ_POSITION":' in source
    assert "self.run_real_position_read()" in source
    assert "[POSITION REAL]" in source
    assert "def update_position_status" in source


def test_hardware_test_console_gui_has_smart_assessment_first_screen():
    source = Path("core/application/hardware_test_console_gui.py").read_text(encoding="utf-8")

    assert "assess_hardware_information" in source
    assert "Smart System Check" in source
    assert "Readiness score" in source
    assert "Recommendation:" in source
    assert "Self-assessment:" in source
    assert "[SMART ASSESSMENT]" in source
    assert "def prepare_motion_test" in source
