from core.education.config_loader import load_config, get_prusa_backend_kwargs


def test_load_config_reads_mk4s_config():
    config = load_config("config/spm_mk4s_config.json")
    assert config["printer"]["port"] == "COM6"
    assert config["printer"]["baudrate"] == 115200


def test_get_prusa_backend_kwargs_extracts_limits():
    config = {
        "printer": {
            "port": "COM6",
            "baudrate": 115200,
        },
        "motion_limits": {
            "x": [0, 250],
            "y": [0, 210],
            "z": [0, 220],
        },
    }

    kwargs = get_prusa_backend_kwargs(config)

    assert kwargs["port"] == "COM6"
    assert kwargs["baudrate"] == 115200
    assert kwargs["x_limits"] == (0, 250)
    assert kwargs["y_limits"] == (0, 210)
    assert kwargs["z_limits"] == (0, 220)


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


def test_get_parking_position():
    from core.education.config_loader import get_parking_position

    config = {
        "parking_position": {
            "x": 1,
            "y": 1,
            "z": 100,
        }
    }

    assert get_parking_position(config) == {"x": 1, "y": 1, "z": 100}


def test_get_scan_mode_preset_reads_hardware_and_z_settings():
    from core.education.config_loader import get_scan_mode_preset

    config = load_config("config/spm_mk4s_config.json")
    preset = get_scan_mode_preset(config, "STM_DEMO")

    assert preset["scan_area"]["x_min"] == 49
    assert preset["scan_area"]["x_max"] == 51
    assert preset["feedrates"]["xy"] == 300
    assert preset["feedrates"]["z"] == 60
    assert preset["z_control"]["feedback"].startswith("constant-current")
    assert preset["hardware"]["z_stage"] == "Original Prusa MK4S Z axis now; fine Z scanner planned later"
    assert preset["hardware"]["sensor"] == "tunneling-current channel planned later"
