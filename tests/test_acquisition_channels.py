from core.acquisition.channels import SimulatedSurfaceChannel, available_default_channels


def test_simulated_surface_channel_returns_synchronized_sample():
    channel = SimulatedSurfaceChannel()

    sample = channel.read_sample(x=50, y=50, z=20)

    assert sample.channel == "simulated_surface"
    assert sample.unit == "a.u."
    assert sample.x == 50.0
    assert sample.y == 50.0
    assert sample.z == 20.0
    assert sample.value > 0.9


def test_default_acquisition_channels_include_safe_simulation():
    channels = available_default_channels()

    assert [channel.name for channel in channels] == ["simulated_surface"]
