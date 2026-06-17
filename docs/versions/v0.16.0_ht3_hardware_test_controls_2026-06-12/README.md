# Educational SPM v0.16.0 - HT3 Hardware Test Controls

Date: 2026-06-12

## Scope

This checkpoint continues the Hardware Test Layer. It adds dry-run-first individual MK4S hardware test controls that can later become GUI buttons.

## Added

- `core/system/hardware_test_controls.py`
- `core/application/hardware_test_control_cli.py`
- `tests/test_hardware_test_controls.py`

## Supported Actions

- `READ_POSITION`
- `SAFE_RETRACT`
- `SAFE_CENTER`
- `X_STEP_PLUS`
- `X_STEP_MINUS`
- `Y_STEP_PLUS`
- `Y_STEP_MINUS`
- `Z_STEP_UP`
- `Z_STEP_DOWN`

## Safety Rules

- Dry-run is default.
- Real movement requires `--execute`.
- `SAFE_CENTER` retracts Z to `120` before moving XY.
- Small-step actions default to 5 mm.
- Confirmed firmware limits are enforced.
- Every action logs to `logs/hardware_test_control_log.csv`.

## Example Dry-Runs

```powershell
.\.venv\Scripts\python.exe -m core.application.hardware_test_control_cli SAFE_CENTER
.\.venv\Scripts\python.exe -m core.application.hardware_test_control_cli X_STEP_PLUS --step-mm 2
```

## First Supervised Real-Motion Commands

Only with a clear hardware path and operator watching:

```powershell
.\.venv\Scripts\python.exe -m core.application.hardware_test_control_cli READ_POSITION --execute
.\.venv\Scripts\python.exe -m core.application.hardware_test_control_cli SAFE_RETRACT --execute
.\.venv\Scripts\python.exe -m core.application.hardware_test_control_cli SAFE_CENTER --execute
```

Then, only after those are correct:

```powershell
.\.venv\Scripts\python.exe -m core.application.hardware_test_control_cli X_STEP_PLUS --step-mm 2 --execute
```

## Verification

- HT3 CLI dry-runs passed.
- Focused HT3 tests passed: 7 tests.
- Full test suite passed: 143 tests.

## Backup

Edited files are backed up in:

`docs/versions/v0.16.0_ht3_hardware_test_controls_2026-06-12/backup/`
