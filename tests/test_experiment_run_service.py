import hashlib
import json

import pytest

from core.system.experiment_run_service import ExperimentRunService
from core.web.spm_scan_simulation import WebScanProfile


def test_completed_run_has_hash_verified_immutable_raw_artifacts(tmp_path) -> None:
    service = ExperimentRunService(tmp_path)
    result = service.execute(run_id="completed", profile=WebScanProfile(x_points=3, y_points=2))

    raw_path = result.run_directory / "raw_samples.jsonl"
    manifest = json.loads((result.run_directory / "manifest.json").read_text(encoding="utf-8"))
    assert result.status == "COMPLETED"
    assert result.sample_count == 6
    assert len(raw_path.read_text(encoding="utf-8").splitlines()) == 6
    assert manifest["safety"] == {"serial_opened": False, "gcode_sent": False, "real_motion_enabled": False}
    assert manifest["artifacts"]["raw_samples.jsonl"] == hashlib.sha256(raw_path.read_bytes()).hexdigest()
    with pytest.raises(FileExistsError, match="immutable"):
        service.execute(run_id="completed", profile=WebScanProfile(x_points=3, y_points=2))


def test_stale_readback_fault_preserves_partial_raw_output_and_event(tmp_path) -> None:
    result = ExperimentRunService(tmp_path).execute(
        run_id="stale", profile=WebScanProfile(x_points=4, y_points=2), fault_mode="stale_readback"
    )

    events = (result.run_directory / "events.jsonl").read_text(encoding="utf-8")
    assert result.status == "FAULTED"
    assert result.sample_count == 4
    assert '"event": "fault_injected"' in events