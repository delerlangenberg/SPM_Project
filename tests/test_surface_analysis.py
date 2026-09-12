"""Unit tests for Stage 9 surface metrology and scientific analysis."""

import math
from pathlib import Path
import tempfile
import numpy as np
import pytest

from core.analysis.surface_analysis import (
    FeatureDetectionResult,
    LineProfile,
    ParticleFeature,
    RoughnessParameters,
    TopographyGrid,
    apply_gaussian_filter,
    apply_median_filter,
    calculate_roughness,
    calculate_step_height,
    detect_particles,
    extract_line_profile,
    level_plane,
    render_profile_plot,
    render_topography_2d,
    render_topography_3d,
    subtract_polynomial_background,
    zero_reference,
)


def test_topography_grid_validation():
    x = np.linspace(20.0, 30.0, 11)
    y = np.linspace(20.0, 30.0, 11)
    z = np.zeros((11, 11))

    grid = TopographyGrid(x_coords=x, y_coords=y, z_matrix=z)
    assert grid.shape == (11, 11)
    assert math.isclose(grid.dx, 1.0)
    assert math.isclose(grid.dy, 1.0)

    # Incompatible shape raises ValueError
    with pytest.raises(ValueError):
        TopographyGrid(x_coords=x, y_coords=y, z_matrix=np.zeros((10, 11)))


def test_plane_leveling():
    # Construct a synthetic tilted plane: Z = 0.05*X - 0.02*Y + 3.0
    x = np.linspace(0.0, 10.0, 21)
    y = np.linspace(0.0, 10.0, 21)
    xm, ym = np.meshgrid(x, y)
    z_tilted = 0.05 * xm - 0.02 * ym + 3.0

    grid = TopographyGrid(x_coords=x, y_coords=y, z_matrix=z_tilted)
    leveled = level_plane(grid)

    # After plane leveling, all values should be virtually 0 (flat)
    residual_std = np.std(leveled.z_matrix)
    assert residual_std < 1e-12
    assert math.isclose(np.ptp(leveled.z_matrix), 0.0, abs_tol=1e-12)


def test_polynomial_background_subtraction():
    # Construct a quadratic surface: Z = 0.002*X^2 + 0.001*Y^2 + 0.0005*X*Y + 0.01*X - 0.02*Y + 1.5
    x = np.linspace(-5.0, 5.0, 25)
    y = np.linspace(-5.0, 5.0, 25)
    xm, ym = np.meshgrid(x, y)
    z_curved = (
        0.002 * (xm**2)
        + 0.001 * (ym**2)
        + 0.0005 * (xm * ym)
        + 0.01 * xm
        - 0.02 * ym
        + 1.5
    )

    grid = TopographyGrid(x_coords=x, y_coords=y, z_matrix=z_curved)
    flattened = subtract_polynomial_background(grid, degree=2)

    residual_std = np.std(flattened.z_matrix)
    assert residual_std < 1e-12


def test_zero_reference():
    x = np.linspace(0, 5, 6)
    y = np.linspace(0, 5, 6)
    z = np.ones((6, 6)) * 42.5

    grid = TopographyGrid(x_coords=x, y_coords=y, z_matrix=z)
    zeroed = zero_reference(grid, method="min")
    assert np.allclose(zeroed.z_matrix, 0.0)


def test_median_filter_despiking():
    x = np.linspace(0, 10, 11)
    y = np.linspace(0, 10, 11)
    z = np.zeros((11, 11))
    # Inject isolated single-pixel spike
    z[5, 5] = 100.0

    grid = TopographyGrid(x_coords=x, y_coords=y, z_matrix=z)
    filtered = apply_median_filter(grid, kernel_size=3)

    # Spike at [5, 5] must be removed
    assert filtered.z_matrix[5, 5] == 0.0
    assert np.allclose(filtered.z_matrix, 0.0)


def test_gaussian_filter_smoothing():
    x = np.linspace(0, 10, 21)
    y = np.linspace(0, 10, 21)
    np.random.seed(42)
    noise = np.random.normal(0, 0.1, (21, 21))

    grid = TopographyGrid(x_coords=x, y_coords=y, z_matrix=noise)
    smoothed = apply_gaussian_filter(grid, sigma=1.0)

    # Smoothing reduces standard deviation of white noise
    assert np.std(smoothed.z_matrix) < np.std(noise)


def test_roughness_parameters_analytical():
    # Analytical verification on sinusoidal surface Z = A * sin(kx)
    amplitude = 0.020  # 20 µm
    x = np.linspace(0, 2 * np.pi, 200)
    y = np.linspace(0, 1, 10)
    xm, _ = np.meshgrid(x, y)
    z_sine = amplitude * np.sin(xm)

    grid = TopographyGrid(x_coords=x, y_coords=y, z_matrix=z_sine)
    roughness = calculate_roughness(grid)

    # Analytical Sa for sine = 2*A / pi ≈ 0.6366 * A
    expected_sa = 2.0 * amplitude / np.pi
    assert math.isclose(roughness.sa_mm, expected_sa, rel_tol=0.01)

    # Analytical Sq for sine = A / sqrt(2) ≈ 0.7071 * A
    expected_sq = amplitude / np.sqrt(2.0)
    assert math.isclose(roughness.sq_mm, expected_sq, rel_tol=0.01)

    # Sz = 2 * amplitude
    assert math.isclose(roughness.sz_mm, 2.0 * amplitude, rel_tol=0.01)

    # Skewness should be ~0 for symmetric sine wave
    assert abs(roughness.ssk) < 0.05


def test_line_profile_and_step_height():
    # Create topography with a step: Z=0 for X < 5.0, Z=0.050 mm (50 µm) for X >= 5.0
    x = np.linspace(0, 10, 101)
    y = np.linspace(0, 10, 101)
    xm, _ = np.meshgrid(x, y)
    z_step = np.where(xm >= 5.0, 0.050, 0.0)

    grid = TopographyGrid(x_coords=x, y_coords=y, z_matrix=z_step)

    # Extract horizontal line profile from (1.0, 5.0) to (9.0, 5.0)
    profile = extract_line_profile(grid, start_xy=(1.0, 5.0), end_xy=(9.0, 5.0), num_points=81)

    assert len(profile.distance_along_profile_mm) == 81
    assert math.isclose(profile.distance_along_profile_mm[-1], 8.0)

    # Measure step height between lower plateau [1.0, 3.0] and upper plateau [5.0, 7.0]
    step_result = calculate_step_height(
        profile,
        lower_plateau_range=(1.0, 3.0),
        upper_plateau_range=(5.0, 7.0),
    )

    assert math.isclose(step_result["step_height_mm"], 0.050, abs_tol=1e-4)
    assert step_result["standard_error_mm"] < 1e-4


def test_particle_detection():
    # Create flat surface with 2 synthetic particle islands
    x = np.linspace(0, 10, 51)
    y = np.linspace(0, 10, 51)
    z = np.zeros((51, 51))

    # Particle 1: 3x3 block at (2.0, 2.0)
    z[9:12, 9:12] = 0.030

    # Particle 2: 4x4 block at (7.0, 7.0)
    z[34:38, 34:38] = 0.060

    grid = TopographyGrid(x_coords=x, y_coords=y, z_matrix=z)

    # Detect features with threshold at 0.010 mm
    result = detect_particles(grid, threshold_z_mm=0.010, min_pixel_area=3)

    assert result.particle_count == 2
    assert len(result.particles) == 2

    # Verify peak heights
    p1 = result.particles[0]
    p2 = result.particles[1]

    # Peak heights relative to threshold (0.010)
    assert math.isclose(p1.peak_height_mm, 0.020, abs_tol=1e-3)
    assert math.isclose(p2.peak_height_mm, 0.050, abs_tol=1e-3)


def test_topography_rendering():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        x = np.linspace(20, 30, 25)
        y = np.linspace(20, 30, 25)
        xm, ym = np.meshgrid(x, y)
        z = 0.01 * np.sin(xm) * np.cos(ym)

        grid = TopographyGrid(x_coords=x, y_coords=y, z_matrix=z)

        p2d = render_topography_2d(grid, tmp_path / "topo2d.png", title="Test 2D Topo")
        p3d = render_topography_3d(grid, tmp_path / "topo3d.png", title="Test 3D Topo")

        profile = extract_line_profile(grid, (20, 20), (30, 30), num_points=30)
        pprof = render_profile_plot(profile, tmp_path / "profile.png", title="Test Profile")

        assert p2d.exists() and p2d.stat().st_size > 1000
        assert p3d.exists() and p3d.stat().st_size > 1000
        assert pprof.exists() and pprof.stat().st_size > 1000

