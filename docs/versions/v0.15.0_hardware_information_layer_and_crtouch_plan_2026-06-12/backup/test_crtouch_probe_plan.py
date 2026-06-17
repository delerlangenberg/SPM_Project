from core.z_control.crtouch_probe_plan import CRTouchProbePlan


def test_crtouch_probe_plan_defaults_to_disabled_real_hardware():
    plan = CRTouchProbePlan()

    assert plan.real_hardware_enabled is False
    assert "DISABLED" in plan.readiness_summary()
    assert "steel needle" in plan.readiness_summary()
    assert "pogo pin" in plan.readiness_summary()
    assert "2x2 mm" in plan.readiness_summary()
    assert "2.0-2.1 mm" in plan.readiness_summary()
    assert "slow Z movement" in plan.safety_summary()
    assert "manual" in plan.test_sequence_summary()
    assert "magnet position" in plan.test_sequence_summary()
