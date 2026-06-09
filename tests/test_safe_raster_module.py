from core.education.safe_raster import generate_grid, make_raster_row, RasterPoint


def test_generate_grid_row_by_row():
    points = list(generate_grid([1, 2], [10, 20]))
    assert points == [
        (1, 10),
        (2, 10),
        (1, 20),
        (2, 20),
    ]


def test_make_raster_row_returns_raster_point():
    state = {
        "position": {
            "x": 48.0,
            "y": 50.0,
            "z": 20.0,
        }
    }

    row = make_raster_row(48, 50, state, 0.25)

    assert isinstance(row, RasterPoint)
    assert row.target_x == 48.0
    assert row.target_y == 50.0
    assert row.actual_x == 48.0
    assert row.actual_y == 50.0
    assert row.actual_z == 20.0
    assert row.simulated_z_signal == 0.25
