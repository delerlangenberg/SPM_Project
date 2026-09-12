import pytest
from unittest.mock import MagicMock, patch
import time

from core.system.deterministic_safety_gate import (
    DeterministicHardwareSafetyGate,
    GateState,
    CoordinateLimits,
)
from core.system.controlled_motion_commissioning import (
    ControlledMotionCommissioning,
)


def test_controlled_motion_commissioning_success():
    gate = DeterministicHardwareSafetyGate()
    gate.enter_read_only()
    assert gate.run_preflight(mk4s_ready=True, arduino_ready=True, operator_confirmed=True) is True

    runner = ControlledMotionCommissioning(safety_gate=gate)

    with patch("serial.Serial") as mock_serial_cls:
        mock_ser = MagicMock()
        mock_serial_cls.return_value.__enter__.return_value = mock_ser
        mock_ser.readline.side_effect = [
            b"ok\n",  # G90
            b"ok\n",  # G1
            b"X:25.00 Y:25.00 Z:120.00 E:0.00 Count X:2500 Y:2500 Z:48000\n",  # M114
        ]

        result = runner.execute_safe_commissioning_jog(
            target_x=25.0,
            target_y=25.0,
            target_z=120.0,
            feedrate_mm_s=10.0,
        )

        assert result.ok is True
        assert result.final_position == {"X": 25.0, "Y": 25.0, "Z": 120.0}
        assert "G1 X25.000 Y25.000 Z120.000 F600.0" in result.commands_executed


def test_controlled_motion_commissioning_bounds_rejection():
    gate = DeterministicHardwareSafetyGate()
    gate.enter_read_only()
    gate.run_preflight(mk4s_ready=True, arduino_ready=True, operator_confirmed=True)

    runner = ControlledMotionCommissioning(safety_gate=gate)

    # Attempt move with X > 80.0 (out of bounds)
    with pytest.raises(ValueError, match="out of safe bounds"):
        runner.execute_safe_commissioning_jog(
            target_x=150.0,
            target_y=25.0,
            target_z=120.0,
        )

    assert gate.state == GateState.FAULT

