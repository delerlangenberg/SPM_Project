import pytest
from core.scan.modes.afm_contact_mode import AfmContactMode

class TestAfmContactMode:
    def test_initialization_default(self):
        mode = AfmContactMode(config={}, hardware_mode=False)
        assert mode.hardware_mode is False
        assert hasattr(mode, 'z_driver')
    
    def test_initialization_with_config(self):
        cfg = {"x_range": 15, "y_range": 20}
        mode = AfmContactMode(config=cfg, hardware_mode=True)
        assert mode.x_range == 15
        assert mode.y_range == 20
        assert mode.hardware_mode is True
