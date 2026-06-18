from core.web.spm_scan_planner import (
    ScanPlanInput,
    X_RESOLUTION_UM,
    Y_RESOLUTION_UM,
    Z_RESOLUTION_UM,
    build_scan_plan_summary,
)


def test_scan_plan_four_image_summary():
    plan = build_scan_plan_summary(
        ScanPlanInput(
            x_min=124.0,
            x_max=126.0,
            y_min=104.0,
            y_max=106.0,
            nx=11,
            ny=11,
            surface_z=55.0,
            clearance_um=500.0,
            seconds_per_point=2.0,
            mode="four_image",
        )
    )

    assert plan["ok"] is True
    assert plan["total_points"] == 484
    assert plan["image_count"] == 4
    assert plan["x_step_um"] == 200.0
    assert plan["y_step_um"] == 200.0
    assert plan["rounded_target_z_mm"] == 55.5
    assert plan["estimated_seconds"] == 968.0


def test_scan_plan_blocks_below_prusa_resolution():
    plan = build_scan_plan_summary(
        ScanPlanInput(x_min=0, x_max=0.01, y_min=0, y_max=1, nx=3, ny=2)
    )

    assert plan["ok"] is False
    assert any("X pixel pitch" in e for e in plan["errors"])


def test_resolution_constants():
    assert X_RESOLUTION_UM == 10.0
    assert Y_RESOLUTION_UM == 10.0
    assert Z_RESOLUTION_UM == 2.5

from core.web.spm_scan_planner import build_raster_preview


def test_raster_preview_four_image_directions():
    preview = build_raster_preview(
        ScanPlanInput(x_min=124.0, x_max=126.0, y_min=104.0, y_max=106.0, nx=3, ny=3)
    )

    assert preview["ok"] is True
    assert preview["directions"] == ["x_plus", "x_minus", "y_plus", "y_minus"]
    assert preview["first_lines"]["x_plus"][0] == {"x_mm": 124.0, "y_mm": 104.0}
    assert preview["first_lines"]["x_plus"][-1] == {"x_mm": 126.0, "y_mm": 104.0}
    assert preview["first_lines"]["x_minus"][0] == {"x_mm": 126.0, "y_mm": 104.0}


def test_raster_preview_rounds_to_prusa_xy_resolution():
    preview = build_raster_preview(
        ScanPlanInput(x_min=124.003, x_max=124.043, y_min=104.004, y_max=104.044, nx=3, ny=3)
    )

    assert preview["ok"] is True
    assert preview["x_positions_mm"] == [124.0, 124.02, 124.04]
    assert preview["y_positions_mm"] == [104.0, 104.02, 104.04]
