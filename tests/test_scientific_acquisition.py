import csv
import json
from pathlib import Path
import pytest
import tempfile

from core.acquisition.scientific_acquisition import (
    MeasurementUncertainty,
    ScientificAcquisitionMetadata,
    ScientificAcquisitionSession,
    ScientificSample,
)


def test_scientific_acquisition_session_lifecycle():
    with tempfile.TemporaryDirectory() as tmpdir:
        base_dir = Path(tmpdir)
        meta = ScientificAcquisitionMetadata(
            acquisition_id="ACQ_20260912_TEST",
            created_at_utc="2026-09-12T15:28:00Z",
            machine_id="13052-4742441644411328",
            machine_type="Prusa-MK4",
            firmware_prusa="Buddy 6.2.4+8909",
            firmware_mega="0.8.7-fast-tap",
            calibration_id="CRT-D3-D8-5OF5",
            operator_id="deler",
            scan_envelope_mm={"X": [20.0, 80.0], "Y": [20.0, 80.0], "Z": [120.0, 150.0]},
            hotend_temp_c=-20.0,
            bed_temp_c=24.8,
            ambient_temp_c=37.9,
        )

        session = ScientificAcquisitionSession(
            acquisition_id="ACQ_20260912_TEST",
            metadata=meta,
            base_dir=base_dir,
        )

        # Record samples
        s1 = session.record_sample(
            x_mm=25.0,
            y_mm=25.0,
            z_mm=120.0,
            trigger_raw=False,
            probe_signal_raw=0.012,
            now_monotonic=100.0,
        )
        s2 = session.record_sample(
            x_mm=26.0,
            y_mm=25.0,
            z_mm=120.0,
            trigger_raw=True,
            trigger_latched=True,
            probe_signal_raw=0.045,
            now_monotonic=100.5,
        )

        assert len(session.samples) == 2
        assert s1.sample_index == 0
        assert s2.sample_index == 1
        assert s1.uncertainty.z_position_uncertainty_mm == 0.0025

        summary = session.finalize_session()
        assert summary["sample_count"] == 2

        # Verify raw JSONL exists and contains valid JSON lines
        assert session.raw_jsonl_path.exists()
        lines = session.raw_jsonl_path.read_text(encoding="utf-8").strip().split("\n")
        assert len(lines) == 2
        d1 = json.loads(lines[0])
        assert d1["x_mm"] == 25.0
        assert d1["y_mm"] == 25.0

        # Verify raw CSV exists and contains rows
        assert session.raw_csv_path.exists()
        with open(session.raw_csv_path, newline="", encoding="utf-8") as f:
            reader = list(csv.DictReader(f))
            assert len(reader) == 2
            assert float(reader[1]["x_mm"]) == 26.0
            assert reader[1]["trigger_latched"] == "True"
