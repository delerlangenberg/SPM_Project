from pathlib import Path

GUI = Path("core/application/gui_scan_launcher.py")


def test_append_log_has_shutdown_guard_for_deleted_qt_widget():
    text = GUI.read_text(encoding="utf-8-sig", errors="replace")

    assert "def append_log(self, message: str) -> None:" in text
    assert "try:" in text
    assert "self.log.append(message)" in text
    assert "except RuntimeError:" in text
    assert "Logging must never crash the GUI." in text
