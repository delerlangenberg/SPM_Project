from pathlib import Path


def test_hardware_test_console_gui_exposes_all_hardware_test_buttons():
    source = Path("core/application/hardware_test_console_gui.py").read_text(encoding="utf-8")

    assert 'APP_VERSION = "v0.17.0"' in source
    assert "HardwareTestConsole" in source
    assert "Read-Only Hardware Information" in source
    assert "Supervised Hardware Test Controls" in source
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
    assert "Confirm supervised real motion" in source
    assert "QMessageBox.warning" in source
    assert "execute=execute" in source


def test_hardware_test_console_gui_keeps_readonly_separate_from_motion():
    source = Path("core/application/hardware_test_console_gui.py").read_text(encoding="utf-8")

    assert "Run real read-only exchange on COM5" in source
    assert "run_real_information_exchange(action)" in source
    assert "run_hardware_test_action" in source
    assert "No motion commands are included." in source
