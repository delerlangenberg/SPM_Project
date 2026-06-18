from core.web.spm_scan_plan_api import build_scan_plan_from_query


def test_scan_plan_api_default_query():
    out = build_scan_plan_from_query("")
    assert out["ok"] is True
    assert out["message"] == "Scan plan calculated."
    assert out["summary"]["total_points"] == 484
    assert out["directions"] == ["x_plus", "x_minus", "y_plus", "y_minus"]


def test_scan_plan_api_blocks_bad_resolution():
    out = build_scan_plan_from_query("x_min=0&x_max=0.01&y_min=0&y_max=1&nx=3&ny=2")
    assert out["ok"] is False
    assert out["message"] == "Scan plan blocked."
    assert any("X pixel pitch" in e for e in out["errors"])
