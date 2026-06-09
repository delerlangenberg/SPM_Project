import csv
from pathlib import Path

from core.education.config_loader import load_config, get_safe_raster_config


def test_safe_raster_csv_exists():
    config = load_config()
    raster = get_safe_raster_config(config)

    path = Path(raster["output_file"])
    assert path.exists()


def test_safe_raster_csv_has_expected_number_of_rows():
    config = load_config()
    raster = get_safe_raster_config(config)
    scan_area = config["scan_area"]

    expected_rows = int(scan_area["x_resolution"]) * int(scan_area["y_resolution"])

    path = Path(raster["output_file"])
    with path.open(newline='') as f:
        rows = list(csv.DictReader(f))

    assert len(rows) == expected_rows


def test_safe_raster_csv_columns():
    config = load_config()
    raster = get_safe_raster_config(config)

    path = Path(raster["output_file"])
    with path.open(newline='') as f:
        reader = csv.DictReader(f)
        assert reader.fieldnames == [
            'timestamp',
            'target_x',
            'target_y',
            'actual_x',
            'actual_y',
            'actual_z',
            'simulated_z_signal',
        ]
