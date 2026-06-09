from core.motion.prusa_gcode_backend import PrusaGcodeBackend
import pytest


def test_parse_m114_extracts_xyz():
	b = PrusaGcodeBackend(port="/dev/null", auto_detect_port=False)
	parsed = b._parse_m114(["X:10.50 Y:20.25 Z:-0.30 E:0.00", "ok"])
	assert parsed["x"] == 10.5
	assert parsed["y"] == 20.25
	assert parsed["z"] == -0.3


def test_move_to_rejects_out_of_limits(monkeypatch):
	b = PrusaGcodeBackend(
		port="/dev/null",
		auto_detect_port=False,
		x_limits=(0.0, 200.0),
		y_limits=(0.0, 200.0),
		z_limits=(0.0, 210.0),
	)

	# Simulate connected backend without touching real serial.
	b._connected = True
	b._ser = object()
	monkeypatch.setattr(b, "send_gcode", lambda *args, **kwargs: ["ok"])

	with pytest.raises(ValueError):
		b.move_to(x=250.0)


def test_move_to_updates_cached_position(monkeypatch):
	b = PrusaGcodeBackend(port="/dev/null", auto_detect_port=False)
	b._connected = True
	b._ser = object()
	monkeypatch.setattr(b, "send_gcode", lambda *args, **kwargs: ["ok"])

	b.move_to(x=12.0, y=5.5)
	state = b.get_state()
	assert state["position"]["x"] == 12.0
	assert state["position"]["y"] == 5.5
