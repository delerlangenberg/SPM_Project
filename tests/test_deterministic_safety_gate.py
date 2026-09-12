import pytest
import time

from core.system.deterministic_safety_gate import (
    DeterministicHardwareSafetyGate,
    GateState,
    CoordinateLimits,
)


def test_gate_initial_state():
    gate = DeterministicHardwareSafetyGate()
    assert gate.state == GateState.DISCONNECTED
    assert gate.fault_reason is None


def test_gate_lifecycle_and_preflight():
    gate = DeterministicHardwareSafetyGate()
    gate.enter_read_only()
    assert gate.state == GateState.READ_ONLY

    # Preflight fails if MK4S or Arduino or Operator not ready
    assert gate.run_preflight(mk4s_ready=False, arduino_ready=True, operator_confirmed=True) is False
    assert gate.state == GateState.FAULT
    assert "Prusa MK4S not ready" in gate.fault_reason

    # Reset with operator acknowledgement
    gate.acknowledge_fault(operator_id="operator_deler")
    assert gate.state == GateState.DISCONNECTED

    gate.enter_read_only()
    assert gate.run_preflight(mk4s_ready=True, arduino_ready=True, operator_confirmed=True) is True
    assert gate.state == GateState.READY


def test_gate_arduino_watchdog_and_stale_feedback():
    gate = DeterministicHardwareSafetyGate(feedback_deadline_s=0.20)
    gate.enter_read_only()
    gate.run_preflight(mk4s_ready=True, arduino_ready=True, operator_confirmed=True)

    t0 = 1000.0

    # Arming without any feedback must fail and latch fault
    with pytest.raises(ConnectionError):
        gate.arm_motion(now_monotonic=t0)
    assert gate.state == GateState.FAULT
    assert "No Arduino feedback" in gate.fault_reason

    # Reset
    gate.acknowledge_fault(operator_id="operator_deler")
    gate.enter_read_only()
    gate.run_preflight(mk4s_ready=True, arduino_ready=True, operator_confirmed=True)

    # Provide valid feedback
    gate.record_arduino_feedback({"identity": "SPM_PROBE_MEGA2560", "state": "READY"}, now_monotonic=t0)
    gate.arm_motion(now_monotonic=t0 + 0.05)
    assert gate.state == GateState.ARMED

    # Authorized move within deadline
    cmd = gate.authorize_linear_move(x=30.0, y=30.0, z=125.0, feedrate_mm_s=10.0, now_monotonic=t0 + 0.10)
    assert cmd == "G1 X30.000 Y30.000 Z125.000 F600.0"
    assert gate.state == GateState.MOTION_AUTHORIZED

    # Move with stale feedback (> 0.20s age) must fail and latch fault
    with pytest.raises(TimeoutError):
        gate.authorize_linear_move(x=35.0, y=30.0, z=125.0, feedrate_mm_s=10.0, now_monotonic=t0 + 0.35)
    assert gate.state == GateState.FAULT
    assert "feedback stale" in gate.fault_reason


def test_gate_coordinate_and_z_floor_bounds():
    gate = DeterministicHardwareSafetyGate()
    gate.enter_read_only()
    gate.run_preflight(mk4s_ready=True, arduino_ready=True, operator_confirmed=True)
    t0 = 100.0
    gate.record_arduino_feedback({"identity": "SPM_PROBE_MEGA2560"}, now_monotonic=t0)
    gate.arm_motion(now_monotonic=t0)

    # Attempt move below safe Z floor (120.0 mm)
    with pytest.raises(ValueError, match="below hard safe floor"):
        gate.authorize_linear_move(x=50.0, y=50.0, z=110.0, feedrate_mm_s=5.0, now_monotonic=t0)
    assert gate.state == GateState.FAULT
    assert "below safe floor" in gate.fault_reason


def test_gate_forbidden_gcode():
    gate = DeterministicHardwareSafetyGate()
    with pytest.raises(PermissionError, match="Prohibited command"):
        gate.filter_raw_gcode("G28 X0 Y0")
    assert gate.state == GateState.FAULT

    with pytest.raises(PermissionError, match="Prohibited command"):
        gate.filter_raw_gcode("M104 S200")


def test_gate_emergency_stop():
    gate = DeterministicHardwareSafetyGate()
    gate.enter_read_only()
    gate.emergency_stop("Physical E-Stop Pressed")
    assert gate.state == GateState.E_STOP

    # Cannot transition or preflight from E_STOP
    with pytest.raises(RuntimeError):
        gate.run_preflight(mk4s_ready=True, arduino_ready=True, operator_confirmed=True)

    gate.acknowledge_fault(operator_id="operator_deler")
    assert gate.state == GateState.DISCONNECTED

