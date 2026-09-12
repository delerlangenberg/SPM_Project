from tools.run_verified_two_magnet_map import (
    RESOLUTION_PROFILES,
    X_MAX,
    X_MIN,
    Y_MAX,
    Y_MIN,
    axis_values,
    map_xy,
    separated_contact_centers,
)


def test_verified_envelope_matches_operator_observation() -> None:
    assert (X_MIN, X_MAX) == (15.5, 250.0)
    assert (Y_MIN, Y_MAX) == (12.5, 210.0)


def test_high_resolution_is_recommended_two_point_five_mm_refinement() -> None:
    assert RESOLUTION_PROFILES["quick"]["focused_pitch_mm"] == 5.0
    assert RESOLUTION_PROFILES["high"]["focused_pitch_mm"] == 2.5
    assert RESOLUTION_PROFILES["research"]["focused_pitch_mm"] == 1.0


def test_axis_values_always_include_verified_endpoint() -> None:
    values = axis_values(15.5, 250.0, 20.0)
    assert values[0] == 15.5
    assert values[-1] == 250.0


def test_map_coordinates_are_operator_facing() -> None:
    assert map_xy(15.5, 210.0) == (0.0, 0.0)
    assert map_xy(250.0, 12.5) == (234.5, 197.5)


def test_spatial_components_discover_unknown_object_count() -> None:
    contacts = [
        (75.5, 72.5),
        (75.5, 92.5),
        (175.5, 132.5),
        (195.5, 132.5),
        (235.5, 32.5),
    ]
    assert separated_contact_centers(contacts, 20.0) == [
        (75.5, 82.5),
        (185.5, 132.5),
        (235.5, 32.5),
    ]
