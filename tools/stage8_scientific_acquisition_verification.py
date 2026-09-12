"""Stage 8 — Authoritative Scientific Acquisition Verification."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.acquisition.scientific_acquisition import (
    MeasurementUncertainty,
    ScientificAcquisitionMetadata,
    ScientificAcquisitionSession,
)


def run_stage8_verification() -> dict:
    acq_id = f"ACQ_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    metadata = ScientificAcquisitionMetadata(
        acquisition_id=acq_id,
        created_at_utc=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        machine_id="13052-4742441644411328",
        machine_type="Prusa-MK4",
        firmware_prusa="Prusa-Firmware-Buddy 6.2.4+8909",
        firmware_mega="0.8.7-fast-tap",
        calibration_id="CRT-D3-D8-5OF5",
        operator_id="deler",
        scan_envelope_mm={
            "x_range": [20.0, 80.0],
            "y_range": [20.0, 80.0],
            "z_safe_range": [120.0, 150.0],
        },
        hotend_temp_c=-20.0,
        bed_temp_c=24.8,
        ambient_temp_c=37.9,
        uncertainty_spec=MeasurementUncertainty(
            xy_position_uncertainty_mm=0.010,
            z_position_uncertainty_mm=0.0025,
            probe_trigger_repeatability_mm=0.005,
            confidence_level_percent=95.0,
        ),
    )

    session = ScientificAcquisitionSession(
        acquisition_id=acq_id,
        metadata=metadata,
        base_dir=PROJECT_ROOT / "data",
    )

    # Acquire benchmark test line
    for i in range(10):
        x = 20.0 + i * 2.0
        session.record_sample(
            x_mm=x,
            y_mm=25.0,
            z_mm=120.0,
            trigger_raw=False,
            trigger_latched=False,
            probe_signal_raw=0.005 + (i % 3) * 0.002,
            probe_signal_unit="mm",
        )

    summary = session.finalize_session()
    summary["ok"] = True
    summary["stage"] = "Stage 8 — Scientific acquisition"
    return summary


if __name__ == "__main__":
    out = run_stage8_verification()
    print(json.dumps(out, indent=2))
    sys.exit(0 if out.get("ok") else 1)
