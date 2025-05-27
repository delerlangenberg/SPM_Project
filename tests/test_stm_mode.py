import pytest
from core.scan.modes.stm_mode import StmMode

class TestStmMode:
    def test_initialization_default(self):
        mode = StmMode(config={}, hardware_mode=False)
        assert mode.hardware_mode is False
        assert hasattr(mode, 'z_driver')

    def test_initialization_with_config(self):
        cfg = {"scan_area": 30}
        mode = StmMode(config=cfg, hardware_mode=True)
        assert mode.scan_area == 30
        assert mode.hardware_mode is True
