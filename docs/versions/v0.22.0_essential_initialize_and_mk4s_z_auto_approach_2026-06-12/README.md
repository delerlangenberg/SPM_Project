# v0.22.0 - Essential Initialize + MK4S Z Auto Approach

Date: 2026-06-12

## Purpose

Fix the main-window crash/annoyance and restore the Z auto-approach path that already worked in Phase 9.

The main software now focuses on the immediate operator path:

1. `INITIALIZE`
2. `Z AUTO APPROACH`
3. `RETRACT Z`
4. Scan only after Z is approached and safe

## Changes

- Version updated to `v0.22.0`.
- Removed automatic Measurement Setup popup on startup.
- Added `core/system/mk4s_z_auto_approach.py`.
- Main `Z AUTO APPROACH` button now runs the confirmed MK4S Phase 9 auto-step approach sequence.
- The sequence moves to Z120, centers at X125/Y105, then steps down to Z56.
- Z remains approached after the sequence; use `RETRACT Z` for safe retract.

## Safety

- The Z auto-approach button requires the critical confirmation popup.
- It should only be used when the foam/sample is placed at the confirmed center and the operator is watching the MK4S.
- The raw serial log is saved to `logs/mk4s_z_auto_approach_raw.txt`.

## Verification

```powershell
.\.venv\Scripts\python.exe -m py_compile core\application\gui_scan_launcher.py core\system\mk4s_z_auto_approach.py
.\.venv\Scripts\python.exe -m pytest tests\test_gui_z_dry_run_safety.py tests\test_mk4s_z_auto_approach.py tests\test_workstation_initializer.py -q
.\.venv\Scripts\python.exe -m pytest -q
```

Results:

- Focused GUI/Z/workstation tests: 46 passed.
- GUI startup smoke test: passed.
- Full project suite: 158 passed.

## Files Changed

- `core/application/gui_scan_launcher.py`
- `core/system/mk4s_z_auto_approach.py`
- `tests/test_gui_z_dry_run_safety.py`
- `tests/test_mk4s_z_auto_approach.py`
- `docs/TWO_LAYER_SPM_DEVELOPMENT_ROADMAP_2026-06-12.md`
