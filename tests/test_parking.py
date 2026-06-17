from core.education.config_loader import get_parking_position, load_config


def test_parking_position_from_config():
    parking = get_parking_position(load_config())

    assert parking == {"x": 1, "y": 1, "z": 100}
