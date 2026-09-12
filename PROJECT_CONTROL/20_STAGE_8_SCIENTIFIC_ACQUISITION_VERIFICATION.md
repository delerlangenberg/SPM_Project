# Stage 8 — Scientific Acquisition Verification

Verified on Spark: 2026-09-12 15:29:12 CEST.
Framework: [`core/acquisition/scientific_acquisition.py`](file:///srv/doro_lab_projects/apps/spm-prusa/core/acquisition/scientific_acquisition.py).
Runner: [`tools/stage8_scientific_acquisition_verification.py`](file:///srv/doro_lab_projects/apps/spm-prusa/tools/stage8_scientific_acquisition_verification.py).

## 1. Scientific Data Invariants Verified
* **Raw / Processed Separation**:
  - Raw immutable streams written to `data/raw/<acquisition_id>/` (both JSONL and CSV).
  - Clean directory reserved for post-acquisition leveled/filtered grids in `data/processed/<acquisition_id>/`.
* **Precision Timestamps & Monotonic Clocks**:
  - Microsecond-resolution UTC timestamps (ISO 8601) and monotonic clock deltas.
* **Physical Units & Dimensions**:
  - Coordinates explicitly stored in millimeters (`mm`).
  - Probe deflection / triggers explicitly stored with units and sensor flags.
* **Uncertainty Tracking**:
  - $XY$ command uncertainty: $\pm 10.0\,\mu\text{m}$ ($0.010\,\text{mm}$).
  - $Z$ command resolution: $\pm 2.5\,\mu\text{m}$ ($0.0025\,\text{mm}$).
  - CR-Touch trigger repeatability: $\pm 5.0\,\mu\text{m}$ ($0.0050\,\text{mm}$) at 95% confidence level.
* **Session Metadata & Provenance**:
  - Machine IDs, firmware versions, calibration IDs (`CRT-D3-D8-5OF5`), operator attribution, and thermal baseline recorded in `metadata.json`.

## 2. Test Verification
* **76 / 76 automated tests passing** (`PYTHONPATH=. .venv/bin/pytest`).
* Validated in [`tests/test_scientific_acquisition.py`](file:///srv/doro_lab_projects/apps/spm-prusa/tests/test_scientific_acquisition.py).
