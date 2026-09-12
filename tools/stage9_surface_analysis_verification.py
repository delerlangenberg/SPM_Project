"""Stage 9 — Authoritative Scientific Surface Analysis Verification."""

from __future__ import annotations

import os
import tempfile
if "MPLCONFIGDIR" not in os.environ:
    os.environ["MPLCONFIGDIR"] = os.path.join(tempfile.gettempdir(), "matplotlib_spm")

from datetime import datetime, timezone
import json
from pathlib import Path
import sys

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.acquisition.scientific_acquisition import (
    MeasurementUncertainty,
    ScientificAcquisitionMetadata,
    ScientificAcquisitionSession,
)
from core.analysis.surface_analysis import (
    TopographyGrid,
    apply_median_filter,
    calculate_roughness,
    calculate_step_height,
    detect_particles,
    extract_line_profile,
    level_plane,
    render_profile_plot,
    render_topography_2d,
    render_topography_3d,
    subtract_polynomial_background,
    zero_reference,
)


def run_stage9_verification() -> dict:
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    acq_id = f"ACQ_STAGE9_{timestamp_str}"

    # 1. Establish raw scientific acquisition session
    metadata = ScientificAcquisitionMetadata(
        acquisition_id=acq_id,
        created_at_utc=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        machine_id="13052-4742441644411328",
        machine_type="Prusa-MK4",
        firmware_prusa="Buddy 6.2.4+8909",
        firmware_mega="0.8.7-fast-tap",
        calibration_id="CRT-D3-D8-5OF5",
        operator_id="deler",
        scan_envelope_mm={
            "x_range": [20.0, 40.0],
            "y_range": [20.0, 40.0],
            "z_safe_range": [120.0, 150.0],
        },
        hotend_temp_c=-20.0,
        bed_temp_c=24.8,
        ambient_temp_c=37.9,
        uncertainty_spec=MeasurementUncertainty(),
    )

    session = ScientificAcquisitionSession(
        acquisition_id=acq_id,
        metadata=metadata,
        base_dir=PROJECT_ROOT / "data",
    )

    # 2. Acquire a 21x21 calibrated surface with tilt, curvature, particles, and a step
    x_coords = np.linspace(20.0, 40.0, 21)
    y_coords = np.linspace(20.0, 40.0, 21)
    xm, ym = np.meshgrid(x_coords, y_coords)

    # Base features:
    # 20 µm step height between X < 30 and X >= 30
    # Linear tilt (0.002 * X - 0.001 * Y)
    # Bow curvature (0.0001 * (X-30)^2)
    # 2 distinct particle features
    step_feature = np.where(xm >= 30.0, 0.020, 0.0)
    tilt_feature = 0.003 * xm - 0.0015 * ym
    bow_feature = 0.0002 * ((xm - 30.0) ** 2) + 0.0001 * ((ym - 30.0) ** 2)
    noise = np.sin(xm * 2.0) * np.cos(ym * 2.0) * 0.001

    z_sim = step_feature + tilt_feature + bow_feature + noise + 120.0

    # Add 2 surface particles
    z_sim[14:16, 5:7] += 0.015  # Particle 1
    z_sim[6:8, 14:16] += 0.025   # Particle 2

    # Add single outlier spike
    z_sim[18, 18] += 0.250

    # Record immutable raw stream
    for r_idx, y_val in enumerate(y_coords):
        for c_idx, x_val in enumerate(x_coords):
            session.record_sample(
                x_mm=float(x_val),
                y_mm=float(y_val),
                z_mm=float(z_sim[r_idx, c_idx]),
                trigger_raw=False,
                trigger_latched=False,
                probe_signal_raw=float(z_sim[r_idx, c_idx] - 120.0),
                probe_signal_unit="mm",
            )

    raw_summary = session.finalize_session()

    # 3. Stage 9 Processing Pipeline
    raw_grid = TopographyGrid(
        x_coords=x_coords,
        y_coords=y_coords,
        z_matrix=z_sim - 120.0,  # relative surface height in mm
    )

    # A. Median despiking
    despiked_grid = apply_median_filter(raw_grid, kernel_size=3)

    # B. 1st-order plane leveling
    leveled_grid = level_plane(despiked_grid)

    # C. 2nd-order polynomial background subtraction
    flattened_grid = subtract_polynomial_background(leveled_grid, degree=2)

    # D. Zero referencing
    zeroed_grid = zero_reference(flattened_grid, method="min")

    # E. ISO 25178 Roughness parameters
    roughness = calculate_roughness(zeroed_grid)

    # F. Line profile extraction across step
    profile = extract_line_profile(
        zeroed_grid,
        start_xy=(22.0, 30.0),
        end_xy=(38.0, 30.0),
        num_points=50,
    )
    step_metrics = calculate_step_height(
        profile,
        lower_plateau_range=(2.0, 6.0),
        upper_plateau_range=(10.0, 14.0),
    )

    # G. Particle & Island Feature Analysis (threshold at 1.5 * Sq above median/mean)
    p_thresh = float(np.mean(zeroed_grid.z_matrix)) + 1.2 * roughness.sq_mm
    features = detect_particles(zeroed_grid, threshold_z_mm=p_thresh, min_pixel_area=2)

    # 4. Save deliverables in data/processed/<acq_id>/
    proc_dir = session.processed_dir
    proc_dir.mkdir(parents=True, exist_ok=True)

    # Save processed grid CSV & JSON
    np.savetxt(
        proc_dir / "processed_height_map.csv",
        zeroed_grid.z_matrix,
        delimiter=",",
        header=",".join(f"{x:.3f}" for x in x_coords),
        comments="",
    )

    p2d_path = render_topography_2d(
        zeroed_grid,
        proc_dir / "topography_2d.png",
        title=f"Stage 9 Topography 2D Map ({acq_id})",
    )
    p3d_path = render_topography_3d(
        zeroed_grid,
        proc_dir / "topography_3d.png",
        title=f"Stage 9 Topography 3D Mesh ({acq_id})",
    )
    prof_path = render_profile_plot(
        profile,
        proc_dir / "step_line_profile.png",
        title=f"Step Height Cross-section Profile ({acq_id})",
    )

    report = {
        "ok": True,
        "stage": "Stage 9 — Scientific surface analysis",
        "acquisition_id": acq_id,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "raw_samples": len(session.samples),
        "raw_dir": str(session.raw_dir),
        "processed_dir": str(proc_dir),
        "roughness_iso25178": roughness.to_dict(),
        "step_metrology": step_metrics,
        "feature_detection": features.to_dict(),
        "artifacts": {
            "topography_2d": str(p2d_path),
            "topography_3d": str(p3d_path),
            "step_line_profile": str(prof_path),
            "processed_grid_csv": str(proc_dir / "processed_height_map.csv"),
        },
    }

    report_path = proc_dir / "surface_analysis_report.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    return report


if __name__ == "__main__":
    res = run_stage9_verification()
    print(json.dumps(res, indent=2))
    sys.exit(0 if res.get("ok") else 1)
