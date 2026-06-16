from pathlib import Path

GUI = Path("core/application/gui_scan_launcher.py")


def test_preview_button_uses_dry_run_pipeline():
    text = GUI.read_text(encoding="utf-8-sig", errors="replace")

    assert 'QPushButton("GENERATE PREVIEW (DRY RUN)")' in text
    assert "No real hardware movement is sent." in text
    assert "self.open_scan_viewer_btn.clicked.connect(self.run_dry_scan)" in text
    assert "self.open_scan_viewer_btn.clicked.connect(self.open_scan_viewer)" not in text
