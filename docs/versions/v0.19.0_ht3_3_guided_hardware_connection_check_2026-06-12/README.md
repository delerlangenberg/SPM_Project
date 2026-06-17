# v0.19.0 - HT3.3 Guided Hardware Connection Check

Date: 2026-06-12

## Purpose

Make the hardware-test console easier to use when the operator is checking whether the MK4S is actually communicating.

The previous log showed repeated `MOTION PREVIEW` entries. That means the software was safe, but the operator could still reasonably expect the hardware to react. This version separates real read-only status checks from supervised movement more clearly.

## Main Changes

- Version updated to `v0.19.0`.
- Phase label updated to `HT3.3 Guided Hardware Connection Check`.
- Read-only hardware exchange defaults to real COM5 status checking.
- Added a connection status display.
- Added an XYZ position status display.
- Added `Run Real Connection Check`.
- Added `Read Current XYZ - Real Safe`.
- `READ_POSITION` can now run real `M114` without unlocking motion.
- X/Y/Z movement actions still require supervised unlock and warning confirmation.

## Operator Flow

1. Press `Run Real Connection Check`.
2. Confirm the connection status turns successful.
3. Press `Read Current XYZ - Real Safe`.
4. Only after the MK4S position is known, unlock supervised real motion for one small axis step at a time.

## Safety Behavior

- Real read-only commands are limited to `M115`, `M105`, `M119`, and `M114`.
- Read-only commands cannot move the MK4S.
- Motion commands still require:
  - check `Enable supervised real motion`
  - type `SUPERVISED`
  - press `EXECUTE SELECTED ON REAL HARDWARE`
  - confirm the warning popup while watching the MK4S

## Launch Command

```powershell
.\.venv\Scripts\python.exe -m core.application.hardware_test_console_gui
```

## Verification

```powershell
.\.venv\Scripts\python.exe -m py_compile core\application\hardware_test_console_gui.py
.\.venv\Scripts\python.exe -m pytest tests\test_hardware_test_console_gui.py tests\test_hardware_test_controls.py tests\test_hardware_information_exchange.py -q
.\.venv\Scripts\python.exe -m pytest -q
```

Results:

- Focused hardware GUI/control/information tests: 17 passed.
- Full project suite: 148 passed.

## Files Changed

- `core/application/hardware_test_console_gui.py`
- `tests/test_hardware_test_console_gui.py`
- `docs/TWO_LAYER_SPM_DEVELOPMENT_ROADMAP_2026-06-12.md`

## Next Phase

HT3.4 should add a guided supervised one-step motion wizard:

- verify connection
- read XYZ
- confirm safe clear area
- move one axis by a small selected step
- read XYZ again
- require operator confirmation before moving the next axis
