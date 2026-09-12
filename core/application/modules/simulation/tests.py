import math

import pytest

from core.application.modules.console_logger import ConsoleLogger
from core.application.modules.simulation import FeedbackSimulator, SampleGenerator, ScannerController, SimulationEngine, SimulationState


@pytest.mark.parametrize("sample_type", SampleGenerator.SAMPLE_TYPES)
def test_all_samples_generate_nonnegative_nonflat_topography(sample_type: str) -> None:
    params = {"height": 1.0, "radius": 1.0, "width": 1.0, "lattice_constant": 0.4,
              "lattice_constant_a": 0.4, "lattice_constant_b": 0.7, "edge_sharpness": 0.1}
    sample = SampleGenerator(sample_type, params)
    grid = sample.get_topography_array(21)
    values = [value for row in grid for value in row]
    assert min(values) >= 0.0
    assert max(values) > min(values)


def test_half_ball_and_square_have_expected_center_and_outside_heights() -> None:
    ball = SampleGenerator("half_ball", {"radius": 1.0, "height": 2.0})
    square = SampleGenerator("square", {"width": 2.0, "height": 3.0, "edge_sharpness": 0.0})
    assert ball.get_height_at_position(0, 0) == pytest.approx(2.0)
    assert ball.get_height_at_position(2, 0) == 0.0
    assert square.get_height_at_position(0, 0) == pytest.approx(3.0)
    assert square.get_height_at_position(2, 0) == 0.0


def test_feedback_is_finite_and_current_decays_with_error() -> None:
    feedback = FeedbackSimulator()
    near = feedback.update(0.1, 0.1, 0.01)
    far = feedback.update(1.0, 0.0, 0.01)
    assert near["current"] > far["current"]
    assert all(math.isfinite(value) for value in far.values())


def test_scanner_respects_acceleration_and_speed_limits_without_noise() -> None:
    scanner = ScannerController(max_speed=10.0, acceleration=20.0, noise_level=0.0, random_source=lambda _a, _b: 0.0)
    first = scanner.move_to(100, 0, 0, 0.1)
    assert first["x"] == pytest.approx(0.2)
    for _ in range(100):
        previous = scanner.position["x"]
        current = scanner.move_to(100, 0, 0, 0.1)
        assert current["x"] - previous <= 1.0 + 1e-9


def test_engine_state_scan_feedback_and_logging() -> None:
    logger = ConsoleLogger()
    scanner = ScannerController(noise_level=0.0, random_source=lambda _a, _b: 0.0)
    engine = SimulationEngine(logger, scanner=scanner)
    assert engine.scan_state is SimulationState.DISABLED
    engine.enable("half_ball", {"radius": 1.0, "height": 0.5})
    assert engine.start_scan({"x_min": -1, "x_max": 1, "y_min": -1, "y_max": 1, "x_points": 8, "y_points": 8})
    point = engine.scan_point(0, 0, z_setpoint=54.0)
    assert point["z"] == pytest.approx(54.5)
    assert set(("deflection", "amplitude", "current", "z_correction")).issubset(point)
    engine.stop_scan()
    engine.disable()
    assert engine.scan_state is SimulationState.DISABLED
    assert all("[SIMULATION]" in record.message for record in logger.snapshot())


def test_engine_never_calls_hardware_and_requires_enable() -> None:
    engine = SimulationEngine()
    with pytest.raises(RuntimeError, match="not enabled"):
        engine.move_to_position(1, 2, 3)
    with pytest.raises(ValueError, match="Unsupported"):
        engine.enable("unknown", {})

