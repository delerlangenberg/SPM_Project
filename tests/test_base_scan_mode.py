import pytest
from core.scan.modes.base_scan_mode import BaseScanMode

class TestBaseScanMode:
    def test_initialization_no_config(self):
        mode = BaseScanMode()
        assert mode.config == {}

    def test_initialization_with_config(self):
        cfg = {"some_key": "some_value"}
        mode = BaseScanMode(config=cfg)
        assert mode.config == cfg
