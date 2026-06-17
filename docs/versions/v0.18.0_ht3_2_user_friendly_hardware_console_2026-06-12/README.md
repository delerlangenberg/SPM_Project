# v0.18.0 - HT3.2 User-Friendly Hardware Test Console

Date: 2026-06-12

## Purpose

Make the hardware test interface clearer for a new operator.

The operator reported that the hardware was not reacting. The log showed that motion actions were still running in dry-run mode, while only read-only information exchange was real. This version changes the wording and button flow so preview and real execution are visibly separate.

## Main Changes

- Version updated to `v0.18.0`.
- Phase label updated to `HT3.2 User-Friendly Hardware Test Console`.
- Added an `About` button in the header.
- Startup log now says preview mode is default and no motion is armed.
- Motion buttons are separated into:
  - `Preview Selected Command`
  - `EXECUTE SELECTED ON REAL HARDWARE`
- Quick buttons are explicitly preview-only.
- Added a large lock-state message:
  - `REAL MOTION LOCKED`
  - `REAL MOTION UNLOCKED`
- If execute is pressed while locked, the software now shows an information popup explaining why the hardware did not move.
- Real motion still requires supervised unlock and confirmation.

## Safety Behavior

Real movement requires all of the following:

1. Check `Enable supervised real motion`.
2. Type `SUPERVISED`.
3. Press `EXECUTE SELECTED ON REAL HARDWARE`.
4. Confirm the warning popup while physically watching the MK4S.

Preview buttons never send motion to hardware.

## Launch Command

```powershell
.\.venv\Scripts\python.exe -m core.application.hardware_test_console_gui
```

## Verification

```powershell
.\.venv\Scripts\python.exe -m py_compile core\application\hardware_test_console_gui.py
.\.venv\Scripts\python.exe -m pytest tests\test_hardware_test_console_gui.py tests\test_hardware_test_controls.py -q
.\.venv\Scripts\python.exe -m pytest -q
```

Results:

- Focused GUI/control tests: 11 passed.
- Full project suite: 147 passed.

## Files Changed

- `core/application/hardware_test_console_gui.py`
- `tests/test_hardware_test_console_gui.py`
- `docs/TWO_LAYER_SPM_DEVELOPMENT_ROADMAP_2026-06-12.md`

## Next Phase

HT3.3 should perform a supervised real-motion check from the v0.18.0 console, starting with read-only information exchange, then `READ_POSITION`, `SAFE_RETRACT`, and one small X/Y/Z step at a time while the operator watches the hardware.
