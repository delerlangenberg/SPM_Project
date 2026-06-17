from core.acquisition.raster_stream import load_raster_frame


def test_raster_stream_loads_existing_safe_raster_output():
    frame = load_raster_frame("data/safe_raster_5x5_output.csv")

    assert frame.point_count == 25
    assert len(frame.latest_line) == 5
    assert "Grid: 5 x 5" in frame.topography_summary()
    assert "Latest line points: 5" in frame.line_scan_summary()
    assert "Latest Y line:" in frame.line_scan_summary()
    assert "Directions:" in frame.line_scan_summary()
    assert "X sweep:" in frame.line_scan_summary()
    assert "Last line preview:" in frame.line_scan_summary()
    assert "Profile:" in frame.line_scan_summary()
    assert len(frame.topography_map_text().splitlines()) == 5
    assert "Z / Signal Feedback" in frame.z_feedback_summary()
    assert "Live X range:" in frame.z_feedback_summary()
    assert "Live Y range:" in frame.z_feedback_summary()
    assert "Scan directions:" in frame.z_feedback_summary()


def test_raster_stream_compresses_long_text_preview():
    from core.acquisition.raster_stream import _render_bar

    assert len(_render_bar([float(index) for index in range(250)])) <= 80
