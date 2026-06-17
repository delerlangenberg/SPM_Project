import sys


def test_plot_cli_accepts_legacy_cmap_alias(tmp_path, monkeypatch):
    from tools import plot_safe_raster

    calls = {}
    output_file = tmp_path / "plot.png"

    def fake_plot_raster(input_file, output_file, color_map):
        calls["input_file"] = input_file
        calls["output_file"] = output_file
        calls["color_map"] = color_map

    monkeypatch.setattr(plot_safe_raster, "plot_raster", fake_plot_raster)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "plot_safe_raster.py",
            "--input-file",
            "data/interface_test_output.csv",
            "--output-file",
            str(output_file),
            "--cmap",
            "plasma",
        ],
    )

    plot_safe_raster.main()

    assert calls == {
        "input_file": "data/interface_test_output.csv",
        "output_file": str(output_file),
        "color_map": "plasma",
    }


def test_plot_cli_uses_safe_5x5_defaults(monkeypatch):
    import sys

    from tools import plot_safe_raster

    calls = {}

    def fake_plot_raster(input_file, output_file, color_map):
        calls["input_file"] = input_file
        calls["output_file"] = output_file
        calls["color_map"] = color_map

    monkeypatch.setattr(plot_safe_raster, "plot_raster", fake_plot_raster)
    monkeypatch.setattr(sys, "argv", ["plot_safe_raster.py"])

    plot_safe_raster.main()

    assert calls == {
        "input_file": "data/safe_raster_5x5_output.csv",
        "output_file": "data/safe_raster_5x5_output.png",
        "color_map": "viridis",
    }
