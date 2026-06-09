from core.education.synthetic_signal import synthetic_surface_signal


def test_synthetic_surface_signal_returns_float():
    value = synthetic_surface_signal(50, 50)
    assert isinstance(value, float)


def test_synthetic_surface_signal_is_repeatable():
    value1 = synthetic_surface_signal(50, 50)
    value2 = synthetic_surface_signal(50, 50)
    assert value1 == value2


def test_synthetic_surface_signal_center_is_stronger_than_far_point():
    center = synthetic_surface_signal(50, 50)
    far = synthetic_surface_signal(48, 48)
    assert center > far
