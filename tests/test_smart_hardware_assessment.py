from core.system.hardware_information_exchange import HardwareInformationResult
from core.system.smart_hardware_assessment import assess_hardware_information, extract_xyz


def result(action: str, command: str, lines: list[str], success: bool = True) -> HardwareInformationResult:
    return HardwareInformationResult(
        action=action,
        command=command,
        success=success,
        response_lines=lines,
        timestamp="2026-06-12T12:00:00",
    )


def test_extract_xyz_from_mk4s_position_line():
    position = extract_xyz(["X:125.00 Y:105.00 Z:120.00 E:73.01 Count X:12500 Y:10500 Z:48000", "ok"])

    assert position == {"x": 125.0, "y": 105.0, "z": 120.0}


def test_smart_assessment_marks_good_readonly_exchange_ready():
    assessment = assess_hardware_information(
        [
            result("IDENTITY", "M115", ["FIRMWARE_NAME: Prusa-Firmware-Buddy", "ok"]),
            result("TEMPERATURE", "M105", ["ok T:24.0 /0.0 B:23.0 /0.0"], True),
            result("ENDSTOPS", "M119", ["x_min: open", "y_min: open", "z_min: open", "ok"]),
            result("POSITION", "M114", ["X:125.00 Y:105.00 Z:120.00 E:0.00", "ok"]),
        ]
    )

    assert assessment.readiness == "READY_FOR_SUPERVISED_MOTION"
    assert assessment.score == 100
    assert "one supervised" in assessment.recommendation
    assert assessment.position == {"x": 125.0, "y": 105.0, "z": 120.0}


def test_smart_assessment_blocks_motion_when_position_missing():
    assessment = assess_hardware_information(
        [
            result("IDENTITY", "M115", ["FIRMWARE_NAME: Prusa-Firmware-Buddy", "ok"]),
            result("TEMPERATURE", "M105", ["ok T:24.0 /0.0 B:23.0 /0.0"], True),
            result("ENDSTOPS", "M119", ["x_min: open", "y_min: open", "z_min: open", "ok"]),
        ]
    )

    assert assessment.readiness == "CHECK_BEFORE_MOTION"
    assert assessment.score == 70
    assert assessment.position is None
