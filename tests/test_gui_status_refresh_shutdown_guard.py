from pathlib import Path

GUI = Path("core/application/gui_scan_launcher.py")


def test_refresh_hardware_parameters_has_shutdown_guard_for_deleted_qt_label():
    text = GUI.read_text(encoding="utf-8-sig", errors="replace")

    assert "def refresh_hardware_parameters(self, phase: str) -> None:" in text
    assert "except RuntimeError:" in text
    assert "Status refresh must not crash." in text
    assert "Hardware parameter refresh ignored during Qt shutdown." in text
