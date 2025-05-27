import pytest
from core.scan.modes.afm_noncontact_mode import AFMNonContactMode

class TestAfmNoncontactMode:
    def test_initialization_default(self):
        mode = AFMNonContactMode(config={}, hardware_mode=False)
        assert mode.hardware_mode is False
        assert hasattr(mode, 'z_driver')
    
    def test_initialization_with_config(self):
        cfg = {"x_range": 12, "y_range": 18}
        mode = AFMNonContactMode(config=cfg, hardware_mode=True)
        assert mode.x_range == 12
        assert mode.y_range == 18
        assert mode.hardware_mode is True
