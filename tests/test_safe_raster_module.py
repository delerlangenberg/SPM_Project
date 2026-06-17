from core.education.safe_raster import generate_grid, generate_bidirectional_grid_from_scan_area, make_raster_row, RasterPoint


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

    row = make_raster_row(48, 50, state, 0.25, scan_direction="backward")

    assert isinstance(row, RasterPoint)
    assert row.scan_direction == "backward"
    assert row.target_x == 48.0
    assert row.target_y == 50.0
    assert row.actual_x == 48.0
    assert row.actual_y == 50.0
    assert row.actual_z == 20.0
    assert row.simulated_z_signal == 0.25


def test_generate_bidirectional_grid_covers_all_spm_directions():
    scan_area = {
        "x_min": 1,
        "x_max": 2,
        "y_min": 10,
        "y_max": 20,
        "x_resolution": 2,
        "y_resolution": 2,
    }

    points = generate_bidirectional_grid_from_scan_area(scan_area)
    directions = [point[2] for point in points]

    assert len(points) == 16
    assert directions.count("forward") == 4
    assert directions.count("backward") == 4
    assert directions.count("upward") == 4
    assert directions.count("downward") == 4
