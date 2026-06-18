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
