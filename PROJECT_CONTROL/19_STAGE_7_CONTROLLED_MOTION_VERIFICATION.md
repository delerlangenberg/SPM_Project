# Stage 7 — Controlled Motion Commissioning Verification

Verified on Spark: 2026-09-12 15:24:50 CEST.
Runner: [`tools/stage7_controlled_motion_commissioning.py`](file:///srv/doro_lab_projects/apps/spm-prusa/tools/stage7_controlled_motion_commissioning.py).
Authority: [`core/system/controlled_motion_commissioning.py`](file:///srv/doro_lab_projects/apps/spm-prusa/core/system/controlled_motion_commissioning.py).

## 1. Verified Commissioning Invariants
* **Central Authority Enforcement**: Motion requested and executed exclusively through `DeterministicHardwareSafetyGate`.
* **Safe Envelope Bounds**:
  - Target: $X=25.0\,\text{mm}$, $Y=25.0\,\text{mm}$, $Z=120.0\,\text{mm}$ (High parking clearance).
  - Velocity: $10.0\,\text{mm/s}$ ($600.0\,\text{mm/min}$).
* **G-code Issued**: `G90`, `G1 X25.000 Y25.000 Z120.000 F600.0`.
* **Zero Homing / Zero Bed Probing**: No unverified `G28` or `G29` commands issued.
* **Arduino Heartbeat**: Active telemetry stream from Arduino Mega verified before arming and move execution.

## 2. Test Verification
* **75 / 75 unit & integration tests passing** (`PYTHONPATH=. .venv/bin/pytest`).
* Automated test coverage in [`tests/test_controlled_motion_commissioning.py`](file:///srv/doro_lab_projects/apps/spm-prusa/tests/test_controlled_motion_commissioning.py).

