import pytest

from core.motion.prusa_gcode_backend import PrusaGcodeBackend


def test_prusa_connect_missing_port_raises():
    b = PrusaGcodeBackend(port="COM_DOES_NOT_EXIST_9999")
    with pytest.raises(Exception):
        b.connect()
