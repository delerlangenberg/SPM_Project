# v0.23.0 - Single Z Scanner + Gwyddion Cleanup

Date: 2026-06-12

## Purpose

Remove redundant Z scanner controls from the main screen.

The main operator workflow must be clean:

1. `INITIALIZE`
2. `Z AUTO APPROACH`
3. `RETRACT Z`
4. scan/data workflow

## Gwyddion Direction

Gwyddion is not hardware-control software; it is an SPM data visualization and analysis environment. The useful lesson is interface discipline:

- keep the active workspace focused on data/status
- put specialized processing in separate tools/modules
- avoid repeating the same operation in multiple places
- make line profiles, topography views, leveling/filtering, and export part of the analysis layer

## Changes

- Version updated to `v0.23.0`.
- Phase label updated to `Essential SPM Workflow - Single Z Scanner`.
- Main window now has one visible `Z Scanner` block.
- The visible Z block contains only:
  - `Z AUTO APPROACH`
  - `RETRACT Z`
- Removed visible main-row duplicates:
  - `CREATE / CONNECT Z SCANNER`
  - `MANUAL Z MOVE`
  - `Z REGULATION`
- Internal helper methods remain available for later expert/debug workflows, but they are no longer part of the main operator path.

## Verification

```powershell
.\.venv\Scripts\python.exe -m py_compile core\application\gui_scan_launcher.py
.\.venv\Scripts\python.exe -m pytest tests\test_gui_z_dry_run_safety.py tests\test_mk4s_z_auto_approach.py -q
.\.venv\Scripts\python.exe -m pytest -q
```

Results:

- Focused GUI/Z tests: 44 passed.
- GUI startup smoke test: passed.
- Full project suite: 158 passed.

## Files Changed

- `core/application/gui_scan_launcher.py`
- `tests/test_gui_z_dry_run_safety.py`
- `docs/TWO_LAYER_SPM_DEVELOPMENT_ROADMAP_2026-06-12.md`
