import math


def synthetic_surface_signal(x, y, *, center_x=50.0, center_y=50.0):
    """
    Generate an educational synthetic SPM signal.

    This simulates a surface with:
    - one smooth central bump
    - small wave-like texture

    It is not real AFM/STM physics.
    It is a safe teaching signal for raster-scan visualization.
    """
    dx = float(x) - center_x
    dy = float(y) - center_y

    bump = math.exp(-((dx * dx + dy * dy) / 8.0))
    texture = 0.15 * math.sin(float(x) * 0.8) * math.cos(float(y) * 0.8)

    return round(bump + texture, 4)
