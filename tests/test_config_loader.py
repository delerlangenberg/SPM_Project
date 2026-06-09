from core.education.config_loader import load_config, get_prusa_backend_kwargs


def test_load_config_reads_mk4s_config():
    config = load_config("config/spm_mk4s_config.json")
    assert config["printer"]["port"] == "COM5"
    assert config["printer"]["baudrate"] == 115200


def test_get_prusa_backend_kwargs_extracts_limits():
    config = {
        "printer": {
            "port": "COM5",
            "baudrate": 115200,
        },
        "motion_limits": {
            "x": [20, 80],
            "y": [20, 80],
            "z": [5, 50],
        },
    }

    kwargs = get_prusa_backend_kwargs(config)

    assert kwargs["port"] == "COM5"
    assert kwargs["baudrate"] == 115200
    assert kwargs["x_limits"] == (20, 80)
    assert kwargs["y_limits"] == (20, 80)
    assert kwargs["z_limits"] == (5, 50)


def test_get_safe_feedrates():
    from core.education.config_loader import get_safe_feedrates

    config = {
        "safe_feedrates": {
            "xy": 1200,
            "z": 300,
        }
    }

    feedrates = get_safe_feedrates(config)

    assert feedrates["xy"] == 1200
    assert feedrates["z"] == 300


def test_get_safe_raster_config():
    from core.education.config_loader import get_safe_raster_config

    config = {
        "safe_raster": {
            "x_points": [48, 50, 52],
            "y_points": [48, 50, 52],
            "scan_z": 20,
            "simulated_z_signal": 0.0,
            "output_file": "data/safe_raster_3x3_output.csv",
        }
    }

    raster = get_safe_raster_config(config)

    assert raster["x_points"] == [48, 50, 52]
    assert raster["y_points"] == [48, 50, 52]
    assert raster["scan_z"] == 20
    assert raster["simulated_z_signal"] == 0.0
    assert raster["output_file"] == "data/safe_raster_3x3_output.csv"
