"""Simulation-only experiment runs with hash-verified raw artifacts."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
from typing import Literal

from core.web.spm_scan_simulation import WebScanProfile, build_scan_line


FaultMode = Literal["none", "stale_readback"]


@dataclass(frozen=True)
class ExperimentRunResult:
    run_id: str
    status: str
    run_directory: Path
    sample_count: int
    fault_mode: FaultMode
    manifest: dict[str, object]


class ExperimentRunService:
    """Owns append-only simulation evidence; it has no hardware dependencies."""

    schema_version = "phase3.simulation-run.v1"

    def __init__(self, run_root: Path) -> None:
        self.run_root = Path(run_root)

    def execute(
        self,
        *,
        run_id: str,
        profile: WebScanProfile | None = None,
        fault_mode: FaultMode = "none",
    ) -> ExperimentRunResult:
        if not run_id or Path(run_id).name != run_id:
            raise ValueError("run_id must be a single non-empty directory name")
        if fault_mode not in {"none", "stale_readback"}:
            raise ValueError("fault_mode must be one of: none, stale_readback")

        profile = profile or WebScanProfile(x_points=8, y_points=4)
        profile.validate()
        run_directory = self.run_root / run_id
        if run_directory.exists():
            raise FileExistsError(f"Experiment run already exists and is immutable: {run_id}")
        run_directory.mkdir(parents=True)

        events = [self._event("run_started", "Simulation-only raster acquisition started.")]
        samples: list[dict[str, object]] = []
        fault_at_sample = (profile.x_points * profile.y_points) // 2
        status = "COMPLETED"

        for line_index in range(profile.y_points):
            line = build_scan_line(profile, line_index)
            for point in line["points"]:
                if fault_mode == "stale_readback" and len(samples) == fault_at_sample:
                    status = "FAULTED"
                    events.append(
                        self._event("fault_injected", "Simulated stale readback detected; acquisition stopped.")
                    )
                    break
                samples.append(
                    {
                        "sample_index": len(samples),
                        "line_index": line_index,
                        "x_mm": point["x"],
                        "y_mm": point["y"],
                        "z_feedback_mm": point["z_feedback"],
                        "surface_height_mm": point["surface_height"],
                        "feedback_error_mm": point["feedback_error"],
                        "source": "simulated_surface",
                    }
                )
            if status == "FAULTED":
                break

        events.append(self._event("run_completed" if status == "COMPLETED" else "run_faulted", status))
        raw_path = run_directory / "raw_samples.jsonl"
        events_path = run_directory / "events.jsonl"
        self._write_jsonl(raw_path, samples)
        self._write_jsonl(events_path, events)
        manifest = {
            "schema_version": self.schema_version,
            "run_id": run_id,
            "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "execution_mode": "SIMULATION_ONLY",
            "status": status,
            "fault_mode": fault_mode,
            "sample_count": len(samples),
            "profile": asdict(profile),
            "safety": {"serial_opened": False, "gcode_sent": False, "real_motion_enabled": False},
            "artifacts": {
                "raw_samples.jsonl": self._sha256(raw_path),
                "events.jsonl": self._sha256(events_path),
            },
        }
        (run_directory / "manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        return ExperimentRunResult(run_id, status, run_directory, len(samples), fault_mode, manifest)

    @staticmethod
    def _event(event: str, detail: str) -> dict[str, str]:
        return {"timestamp": datetime.now(timezone.utc).isoformat(timespec="milliseconds"), "event": event, "detail": detail}

    @staticmethod
    def _write_jsonl(path: Path, records: list[dict[str, object]]) -> None:
        path.write_text("".join(json.dumps(record, sort_keys=True) + "\n" for record in records), encoding="utf-8")

    @staticmethod
    def _sha256(path: Path) -> str:
        return sha256(path.read_bytes()).hexdigest()