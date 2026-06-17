# v0.24.0 - Connect, Approach, Measurement Main Page

Date: 2026-06-12

## Purpose

Restructure the main page into the exact operator workflow:

1. SPM Connection
2. Approach
3. Measurement

Hardware check is now treated as a service/tool function, not a normal user action on the main page.

## Main Page

### SPM Connection

- `CONNECT TO SPM`
- `DISCONNECT`

### Approach

- setpoint above surface in mm
- manual step in mm
- `MANUAL UP`
- `MANUAL DOWN`
- `Z AUTO APPROACH`
- `RETRACT Z`

### Measurement

- X/Y min/max
- X/Y point count
- `START`
- `PAUSE`
- `STOP`
- `X+ TOPOGRAPHY`
- `X- TOPOGRAPHY`
- `Y+ TOPOGRAPHY`
- `Y- TOPOGRAPHY`

## Verification

```powershell
.\.venv\Scripts\python.exe -m py_compile core\application\gui_scan_launcher.py core\system\mk4s_z_auto_approach.py
.\.venv\Scripts\python.exe -m pytest tests\test_gui_z_dry_run_safety.py tests\test_mk4s_z_auto_approach.py -q
.\.venv\Scripts\python.exe -m pytest -q
```

Results:

- Focused GUI/Z tests: 46 passed.
- GUI startup smoke test: passed.
- Full project suite: 160 passed.

## Files Changed

- `core/application/gui_scan_launcher.py`
- `core/system/mk4s_z_auto_approach.py`
- `tests/test_gui_z_dry_run_safety.py`
- `tests/test_mk4s_z_auto_approach.py`
- `docs/TWO_LAYER_SPM_DEVELOPMENT_ROADMAP_2026-06-12.md`
