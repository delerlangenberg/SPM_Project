from __future__ import annotations

from urllib.parse import parse_qs

from core.web.spm_scan_planner import ScanPlanInput, build_raster_preview


def _float_arg(qs: dict, name: str, default: float) -> float:
    try:
        return float(qs.get(name, [default])[0])
    except Exception:
        return default


def _int_arg(qs: dict, name: str, default: int) -> int:
    try:
        return int(qs.get(name, [default])[0])
    except Exception:
        return default


def build_scan_plan_from_query(query: str) -> dict:
    qs = parse_qs(query or "")

    mode = qs.get("mode", ["four_image"])[0]
    if mode not in {"x_fast", "y_fast", "four_image"}:
        mode = "four_image"

    inp = ScanPlanInput(
        x_min=_float_arg(qs, "x_min", 124.0),
        x_max=_float_arg(qs, "x_max", 126.0),
        y_min=_float_arg(qs, "y_min", 104.0),
        y_max=_float_arg(qs, "y_max", 106.0),
        nx=_int_arg(qs, "nx", 11),
        ny=_int_arg(qs, "ny", 11),
        surface_z=_float_arg(qs, "surface_z", 55.0),
        clearance_um=_float_arg(qs, "clearance_um", 500.0),
        seconds_per_point=_float_arg(qs, "seconds_per_point", 2.0),
        mode=mode,
    )

    preview = build_raster_preview(inp)
    preview["message"] = "Scan plan calculated." if preview.get("ok") else "Scan plan blocked."
    return preview
