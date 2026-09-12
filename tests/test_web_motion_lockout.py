from core.web.real_scan_control import run_real_constant_z_scan
from core.web.spm_scan_simulation import WebScanProfile
from core.web.system_control import system_health_test
from core.web.z_scanner_control import z_manual_step


def test_environment_flags_cannot_enable_real_scan(monkeypatch) -> None:
    monkeypatch.setenv("SPM_WEB_ALLOW_REAL_SCAN", "1")
    result = run_real_constant_z_scan(WebScanProfile(x_points=2, y_points=1))
    assert result["status"] == "motion_locked"
    assert "safety supervisor" in result["message"]


def test_environment_flags_cannot_enable_z_motion(monkeypatch) -> None:
    monkeypatch.setenv("SPM_WEB_ALLOW_Z_MOTION", "1")
    result = z_manual_step(direction="down", step_mm=0.1, confirmed=True)
    assert result["status"] == "motion_locked"
    assert "safety supervisor" in result["message"]


def test_environment_flags_cannot_enable_health_motion(monkeypatch) -> None:
    monkeypatch.setenv("SPM_WEB_ALLOW_HEALTH_MOTION", "1")
    result = system_health_test(confirmed="1", motion="1")
    assert result["status"] == "blocked"
    assert "safety supervisor" in result["message"]