from core.system.hardware_diagnostics import (
    HardwareCheck,
    HardwareDiagnosticReport,
    check_motion_envelope,
)
from core.education.config_loader import load_config


def test_hardware_report_fails_on_failed_check():
    report = HardwareDiagnosticReport(
        checks=(
            HardwareCheck("A", "PASS", "ok"),
            HardwareCheck("B", "FAIL", "bad"),
        )
    )

    assert report.passed is False
    assert "FAIL: B - bad" in report.summary_text()


def test_hardware_report_allows_warning_for_known_missing_z_controller():
    report = HardwareDiagnosticReport(
        checks=(
            HardwareCheck("A", "PASS", "ok"),
            HardwareCheck("Z", "WARN", "not mounted yet"),
        )
    )

    assert report.passed is True
    assert "Overall: PASS" in report.summary_text()


def test_motion_envelope_check_reports_configured_limits():
    check = check_motion_envelope(load_config())

    assert check.status == "PASS"
    assert "Original MK4S machine limits" in check.message
    assert any("Machine limits" in detail for detail in check.details)
    assert any("SPM-safe" in detail for detail in check.details)
