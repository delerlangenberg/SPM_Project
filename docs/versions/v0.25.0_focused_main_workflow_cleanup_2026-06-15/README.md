# v0.25.0 - Focused Main Workflow Cleanup

Date: 2026-06-15

Goal:

- Remove the feeling of multiple competing Z scanner workflows.
- Keep the normal operator page limited to connection, approach, and measurement.
- Follow the Gwyddion-style lesson: focused main workspace, modular specialist tools.

Visible main workflow:

- SPM Connection
  - `CONNECT TO SPM`
  - `DISCONNECT`
- Approach
  - setpoint above surface
  - manual step
  - `MANUAL UP`
  - `MANUAL DOWN`
  - `Z AUTO APPROACH`
  - `RETRACT Z`
- Measurement
  - XY range and point count
  - `START`
  - `PAUSE`
  - `STOP`
  - `X+ TOPOGRAPHY`
  - `X- TOPOGRAPHY`
  - `Y+ TOPOGRAPHY`
  - `Y- TOPOGRAPHY`

Changed:

- Version updated to `v0.25.0`.
- Phase label updated to `Focused SPM Workflow - Connection, Approach, Measurement`.
- Main-page status is inside `SPM Connection`.
- Main-page wording now says `Approach`, not `Z Scanner`.
- Hidden diagnostic naming changed from `Z Regulation` to `Service Approach Diagnostics`.
- Hardware/service controls remain outside the normal operator path.

Verification:

- `python -m py_compile core\application\gui_scan_launcher.py core\system\mk4s_z_auto_approach.py`
- `pytest tests\test_gui_z_dry_run_safety.py tests\test_mk4s_z_auto_approach.py -q`
  - 46 passed
- `pytest -q`
  - 160 passed

Screenshot:

- `data\v0.25.0_focused_main_workflow_window.png`
