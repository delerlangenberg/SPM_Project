from core.system.hardware_diagnostics import HardwareCheck, HardwareDiagnosticReport
from core.system.hardware_information_exchange import HardwareInformationResult
from core.system.workstation_initializer import run_workstation_initialization


class FakeZDriver:
    def __init__(self):
        self.connected = False

    def connect(self):
        self.connected = True
        return True


def info_result(action: str, command: str, lines: list[str]) -> HardwareInformationResult:
    return HardwareInformationResult(
        action=action,
        command=command,
        success=True,
        response_lines=lines,
        timestamp="2026-06-12T12:00:00",
    )


def good_information(_action: str) -> list[HardwareInformationResult]:
    return [
        info_result("IDENTITY", "M115", ["FIRMWARE_NAME: Prusa-Firmware-Buddy", "ok"]),
        info_result("TEMPERATURE", "M105", ["ok T:24.0 /0.0 B:23.0 /0.0"]),
        info_result("ENDSTOPS", "M119", ["x_min: open", "y_min: open", "z_min: open", "ok"]),
        info_result("POSITION", "M114", ["X:125.00 Y:105.00 Z:120.00 E:0.00", "ok"]),
    ]


def test_workstation_initialization_passes_with_diagnostics_assessment_and_z_ready():
    report = HardwareDiagnosticReport((HardwareCheck("MK4S", "PASS", "ok"),))

    result = run_workstation_initialization(
        {"printer": {"port": "COM5"}},
        FakeZDriver(),
        diagnostic_runner=lambda _config: report,
        information_runner=good_information,
    )

    assert result.passed is True
    assert result.ready_state == "SYSTEM READY"
    assert result.z_ready is True
    assert result.assessment.score == 100
    assert any("Z scanner layer: READY" in line for line in result.summary_lines)


def test_workstation_initialization_fails_when_diagnostic_fails():
    report = HardwareDiagnosticReport((HardwareCheck("MK4S", "FAIL", "no response"),))

    result = run_workstation_initialization(
        {"printer": {"port": "COM5"}},
        FakeZDriver(),
        diagnostic_runner=lambda _config: report,
        information_runner=good_information,
    )

    assert result.passed is False
    assert result.ready_state == "INITIALIZATION FAILED"
    assert result.assessment.readiness == "READY_FOR_SUPERVISED_MOTION"
