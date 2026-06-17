import json

from core.acquisition.scan_session import (
    build_scan_session_metadata,
    metadata_path_for_output,
    write_scan_session_metadata,
)
from core.education.scan_profile import ScanProfile


def profile():
    return ScanProfile(
        x_min=46,
        x_max=54,
        y_min=46,
        y_max=54,
        z=20,
        x_resolution=5,
        y_resolution=5,
        feedrate_xy=1200,
        feedrate_z=300,
        mode="SIMULATED_SURFACE",
    )


def test_build_scan_session_metadata_contains_traceability_fields():
    metadata = build_scan_session_metadata(
        profile=profile(),
        output_file="data/out.csv",
        point_count=25,
        execution_mode="DRY_RUN",
        channel="simulated_surface",
    )

    assert metadata["execution_mode"] == "DRY_RUN"
    assert metadata["channel"] == "simulated_surface"
    assert metadata["point_count"] == 25
    assert metadata["scan_profile"]["x_resolution"] == 5


def test_metadata_path_for_output_uses_sidecar_json():
    assert str(metadata_path_for_output("data/out.csv")) == "data\\out.metadata.json"


def test_write_scan_session_metadata_writes_json(tmp_path):
    output_file = tmp_path / "scan.csv"

    metadata_path = write_scan_session_metadata(
        profile=profile(),
        output_file=str(output_file),
        point_count=25,
        execution_mode="DRY_RUN",
        channel="simulated_surface",
    )

    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert metadata["output_file"] == str(output_file)
    assert metadata["point_count"] == 25
