import pytest

from core.system.safety_supervisor import SafetyState, SafetySupervisor


def test_simulation_lifecycle_is_explicit_and_motion_free() -> None:
    supervisor = SafetySupervisor()
    supervisor.enter_read_only()
    supervisor.complete_preflight(passed=True)
    supervisor.arm_simulation()
    supervisor.start_simulation_acquisition()
    supervisor.begin_retract()
    supervisor.complete_retract()

    snapshot = supervisor.snapshot()
    assert supervisor.state is SafetyState.READY
    assert snapshot["real_motion_enabled"] is False
    assert snapshot["serial_opened"] is False
    assert snapshot["gcode_sent"] is False


def test_acquisition_cannot_start_without_arming() -> None:
    supervisor = SafetySupervisor()
    with pytest.raises(RuntimeError, match="invalid from DISCONNECTED"):
        supervisor.start_simulation_acquisition()


def test_failed_preflight_requires_retract_before_recovery() -> None:
    supervisor = SafetySupervisor()
    supervisor.enter_read_only()
    supervisor.complete_preflight(passed=False)
    assert supervisor.state is SafetyState.FAULT
    with pytest.raises(RuntimeError, match="invalid from FAULT"):
        supervisor.enter_read_only()
    supervisor.begin_retract()
    supervisor.complete_retract()
    assert supervisor.state is SafetyState.READY


def test_emergency_stop_requires_explicit_acknowledgement() -> None:
    supervisor = SafetySupervisor()
    supervisor.emergency_stop("test stop")
    with pytest.raises(RuntimeError, match="invalid from E_STOP"):
        supervisor.enter_read_only()
    supervisor.acknowledge_emergency_stop()
    assert supervisor.state is SafetyState.DISCONNECTED


def test_real_motion_is_denied_in_all_states() -> None:
    supervisor = SafetySupervisor()
    with pytest.raises(PermissionError, match="permanently disabled"):
        supervisor.authorize_real_motion()