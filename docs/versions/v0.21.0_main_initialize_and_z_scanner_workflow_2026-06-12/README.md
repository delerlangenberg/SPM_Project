# v0.21.0 - Main Initialize + Z Scanner Workflow

Date: 2026-06-12

## Purpose

Move the project forward from troubleshooting toward the real operator workflow.

The troubleshooting console remains useful, but the main software must be simple:

1. Press `INITIALIZE`.
2. Software performs the complete no-motion hardware and readiness check.
3. If passed, the main banner changes to `SYSTEM READY`.
4. Operator proceeds to Z scanner move, auto approach, or retract.

## Main Changes

- Main GUI version updated to `v0.21.0`.
- Phase label updated to `Main Workflow - One Button Initialize + Z Scanner`.
- Main initialization button renamed to `INITIALIZE`.
- Added backend `core/system/workstation_initializer.py`.
- One-button initialization now performs:
  - scan-profile validation
  - MK4S no-motion diagnostics
  - read-only identity/status/endstop/position checks
  - local smart readiness assessment
  - dry-run Z scanner creation/connection
- Success state is now `SYSTEM STATUS: SYSTEM READY`.
- Added main-window `Z Scanner / Approach` panel.
- Promoted Z workflow buttons:
  - `CREATE / CONNECT Z SCANNER`
  - `MANUAL Z MOVE`
  - `AUTO APPROACH`
  - `RETRACT Z`

## Safety Behavior

- Initialization performs no movement.
- Real motion remains disabled after initialization.
- The current Z scanner workflow uses the existing safe dry-run Z layer.
- Fine/real Z scanner hardware must be mounted and verified before real Z control is enabled.

## Launch Command

```powershell
.\.venv\Scripts\python.exe -m core.application.gui_scan_launcher
```

## Verification

```powershell
.\.venv\Scripts\python.exe -m py_compile core\application\gui_scan_launcher.py core\system\workstation_initializer.py
.\.venv\Scripts\python.exe -m pytest tests\test_workstation_initializer.py tests\test_gui_z_dry_run_safety.py tests\test_workstation_status.py -q
.\.venv\Scripts\python.exe -m pytest -q
```

Results:

- Focused workflow tests: 47 passed.
- Full project suite: 155 passed.

## Files Changed

- `core/application/gui_scan_launcher.py`
- `core/system/workstation_initializer.py`
- `tests/test_gui_z_dry_run_safety.py`
- `tests/test_workstation_initializer.py`
- `docs/TWO_LAYER_SPM_DEVELOPMENT_ROADMAP_2026-06-12.md`

## Next Phase

M0.2 should replace the dry-run Z layer with a hardware-ready Z scanner interface that can support the planned CR-Touch/contact-probe subsystem once the physical electronics are installed and confirmed.
