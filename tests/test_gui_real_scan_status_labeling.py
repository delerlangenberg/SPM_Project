from pathlib import Path

GUI = Path("core/application/gui_scan_launcher.py")


def test_real_hardware_scan_status_is_explicit_about_blocking_cli_and_preview_refresh():
    text = GUI.read_text(encoding="utf-8-sig", errors="replace")

    assert "REAL MK4S motion running via blocking CLI" in text
    assert "preview updates after CSV/plot generation" in text
    assert "Measurement values: configured raster pipeline / simulated surface unless a real sensor backend is active" in text
    assert "Live point-by-point hardware visualization: planned for the next integration phase" in text
    assert "Real scan complete: output CSV and raster preview were refreshed" in text
    assert "Real scan failed: blocking CLI returned exit code" in text
