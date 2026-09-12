import ast
from pathlib import Path

import pytest

from core.ai.safety_learning_advisor import SafetyLearningAdvisor


def test_advisory_only(tmp_path):
    advisor = SafetyLearningAdvisor(tmp_path / "history.jsonl")

    result = advisor.recommend(error="serial timeout")

    assert result["advisory_only"] is True
    assert result["execution_allowed"] is False
    assert result["hardware_access"] is False
    assert result["error_type"] == "communication_timeout"


def test_requires_operator_verified_learning(tmp_path):
    advisor = SafetyLearningAdvisor(tmp_path / "history.jsonl")

    with pytest.raises(PermissionError):
        advisor.record_outcome(
            error_type="communication_timeout",
            recommendation_id="retry_readonly",
            success=True,
            operator_verified=False,
        )


def test_learning_changes_ranking(tmp_path):
    advisor = SafetyLearningAdvisor(tmp_path / "history.jsonl")

    for _ in range(20):
        advisor.record_outcome(
            error_type="communication_timeout",
            recommendation_id="retry_readonly",
            success=False,
            operator_verified=True,
        )

    for _ in range(20):
        advisor.record_outcome(
            error_type="communication_timeout",
            recommendation_id="explicit_port",
            success=True,
            operator_verified=True,
        )

    result = advisor.recommend(error="timeout")

    assert (
        result["top_recommendation"]["recommendation_id"]
        == "explicit_port"
    )


def test_probe_motion_anomaly_is_flagged(tmp_path):
    advisor = SafetyLearningAdvisor(tmp_path / "history.jsonl")

    result = advisor.recommend(
        error="probe status",
        context={
            "connected": True,
            "authorization_state": "STANDBY",
            "probe_state": "CONTACT / TRIGGERED",
            "requested_action": "Z approach",
        },
    )

    assert (
        "probe_triggered_before_requested_motion"
        in result["safety_flags"]
    )

    assert result["requires_operator_review"] is True


def test_invalid_operational_state_is_flagged(tmp_path):
    advisor = SafetyLearningAdvisor(tmp_path / "history.jsonl")

    result = advisor.recommend(
        error="calibration",
        context={
            "connected": False,
            "authorization_state": "OPERATIONAL",
            "calibration_valid": False,
        },
    )

    assert (
        "motion_authorization_without_connection"
        in result["safety_flags"]
    )

    assert (
        "operational_without_valid_calibration"
        in result["safety_flags"]
    )


def test_no_hardware_imports():
    source = Path(
        "core/ai/safety_learning_advisor.py"
    ).read_text(encoding="utf-8")

    tree = ast.parse(source)

    imported = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(x.name for x in node.names)

        elif isinstance(node, ast.ImportFrom):
            imported.append(node.module or "")

    forbidden = (
        "serial",
        "subprocess",
        "core.hardware",
        "core.motion",
        "core.web",
        "core.ai.academic_gcode_generator",
    )

    assert not any(
        module == blocked
        or module.startswith(blocked + ".")
        for module in imported
        for blocked in forbidden
    )
