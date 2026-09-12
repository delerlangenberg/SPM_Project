"""Stage 8 — Scientific Acquisition Framework.

Implements:
- Structured, immutable raw acquisition data streams (JSONL & CSV).
- High-precision ISO 8601 & monotonic timestamping.
- Explicit physical units and uncertainty records.
- Comprehensive acquisition metadata (Machine ID, Firmware, Calibration IDs, Operator ID, Temperatures).
- Strict architectural separation between raw immutable data and processed datasets.
"""

from __future__ import annotations

import csv
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import json
from pathlib import Path
import time
from typing import Any, Optional


@dataclass(frozen=True)
class MeasurementUncertainty:
    xy_position_uncertainty_mm: float = 0.010  # 10 µm command resolution
    z_position_uncertainty_mm: float = 0.0025  # 2.5 µm command resolution
    probe_trigger_repeatability_mm: float = 0.0050  # 5 µm CR-Touch repeatability
    confidence_level_percent: float = 95.0


@dataclass(frozen=True)
class ScientificSample:
    sample_index: int
    timestamp_utc: str
    timestamp_monotonic: float
    x_mm: float
    y_mm: float
    z_mm: float
    trigger_raw: bool
    trigger_latched: bool
    probe_signal_raw: float
    probe_signal_unit: str
    uncertainty: MeasurementUncertainty = field(default_factory=MeasurementUncertainty)


@dataclass(frozen=True)
class ScientificAcquisitionMetadata:
    acquisition_id: str
    created_at_utc: str
    machine_id: str
    machine_type: str
    firmware_prusa: str
    firmware_mega: str
    calibration_id: str
    operator_id: str
    scan_envelope_mm: dict[str, list[float]]
    hotend_temp_c: float
    bed_temp_c: float
    ambient_temp_c: float
    uncertainty_spec: MeasurementUncertainty = field(default_factory=MeasurementUncertainty)


class ScientificAcquisitionSession:
    """Manages an active scientific acquisition session with raw/processed separation."""

    def __init__(
        self,
        acquisition_id: str,
        metadata: ScientificAcquisitionMetadata,
        base_dir: Path = Path("/srv/doro_lab_projects/apps/spm-prusa/data"),
    ) -> None:
        self.acquisition_id = acquisition_id
        self.metadata = metadata
        self.base_dir = base_dir
        self.raw_dir = base_dir / "raw" / acquisition_id
        self.processed_dir = base_dir / "processed" / acquisition_id
        self.samples: list[ScientificSample] = []
        self._sample_counter = 0

        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)

        # Write immutable session metadata
        metadata_file = self.raw_dir / "metadata.json"
        metadata_file.write_text(
            json.dumps(asdict(self.metadata), indent=2),
            encoding="utf-8",
        )

    @property
    def raw_jsonl_path(self) -> Path:
        return self.raw_dir / "acquisition_stream.jsonl"

    @property
    def raw_csv_path(self) -> Path:
        return self.raw_dir / "acquisition_stream.csv"

    def record_sample(
        self,
        *,
        x_mm: float,
        y_mm: float,
        z_mm: float,
        trigger_raw: bool = False,
        trigger_latched: bool = False,
        probe_signal_raw: float = 0.0,
        probe_signal_unit: str = "mm",
        now_monotonic: Optional[float] = None,
    ) -> ScientificSample:
        """Records an immutable scientific measurement sample."""
        now_mono = time.monotonic() if now_monotonic is None else now_monotonic
        now_iso = datetime.now(timezone.utc).isoformat(timespec="microseconds")

        sample = ScientificSample(
            sample_index=self._sample_counter,
            timestamp_utc=now_iso,
            timestamp_monotonic=now_mono,
            x_mm=float(x_mm),
            y_mm=float(y_mm),
            z_mm=float(z_mm),
            trigger_raw=bool(trigger_raw),
            trigger_latched=bool(trigger_latched),
            probe_signal_raw=float(probe_signal_raw),
            probe_signal_unit=probe_signal_unit,
        )
        self._sample_counter += 1
        self.samples.append(sample)

        # Append to raw JSONL stream
        with open(self.raw_jsonl_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(sample)) + "\n")

        return sample

    def finalize_session(self) -> dict[str, Any]:
        """Finalizes raw CSV export and writes manifest."""
        # Export complete raw CSV
        if self.samples:
            fieldnames = [
                "sample_index",
                "timestamp_utc",
                "timestamp_monotonic",
                "x_mm",
                "y_mm",
                "z_mm",
                "trigger_raw",
                "trigger_latched",
                "probe_signal_raw",
                "probe_signal_unit",
                "xy_position_uncertainty_mm",
                "z_position_uncertainty_mm",
                "probe_trigger_repeatability_mm",
            ]
            with open(self.raw_csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for s in self.samples:
                    row = {
                        "sample_index": s.sample_index,
                        "timestamp_utc": s.timestamp_utc,
                        "timestamp_monotonic": s.timestamp_monotonic,
                        "x_mm": s.x_mm,
                        "y_mm": s.y_mm,
                        "z_mm": s.z_mm,
                        "trigger_raw": s.trigger_raw,
                        "trigger_latched": s.trigger_latched,
                        "probe_signal_raw": s.probe_signal_raw,
                        "probe_signal_unit": s.probe_signal_unit,
                        "xy_position_uncertainty_mm": s.uncertainty.xy_position_uncertainty_mm,
                        "z_position_uncertainty_mm": s.uncertainty.z_position_uncertainty_mm,
                        "probe_trigger_repeatability_mm": s.uncertainty.probe_trigger_repeatability_mm,
                    }
                    writer.writerow(row)

        summary = {
            "acquisition_id": self.acquisition_id,
            "sample_count": len(self.samples),
            "raw_jsonl": str(self.raw_jsonl_path),
            "raw_csv": str(self.raw_csv_path),
            "raw_metadata": str(self.raw_dir / "metadata.json"),
            "processed_dir": str(self.processed_dir),
            "completed_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }

        manifest_path = self.raw_dir / "session_manifest.json"
        manifest_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
        return summary
