import pytest
from core.scan.modes.profiling_mode import ProfilingMode

class TestProfilingMode:
    def test_initialization_default(self):
        mode = ProfilingMode(config={}, hardware_mode=False)
        assert mode.hardware_mode is False
        assert hasattr(mode, 'z_driver')

    def test_initialization_with_config(self):
        cfg = {"profile_length": 150}
        mode = ProfilingMode(config=cfg, hardware_mode=True)
        assert mode.profile_length == 150
        assert mode.hardware_mode is True
