# Educational SPM v0.17.0 - HT3.1 Hardware Test Console GUI

Date: 2026-06-12

## Scope

This phase adds a small dedicated interface for the Hardware Test Layer. It avoids the unstable measurement GUI and focuses only on power/status/information exchange and supervised hardware test controls.

## Added

- `core/application/hardware_test_console_gui.py`
- `tests/test_hardware_test_console_gui.py`

## Interface Command

```powershell
.\.venv\Scripts\python.exe -m core.application.hardware_test_console_gui
```

## Interface Sections

### 1 Read-Only Hardware Information

Actions:

- `ALL`
- `IDENTITY`
- `TEMPERATURE`
- `ENDSTOPS`
- `POSITION`

Real read-only exchange is optional and sends only information commands.

### 2 Supervised Hardware Test Controls

Actions:

- `READ_POSITION`
- `SAFE_RETRACT`
- `SAFE_CENTER`
- `X_STEP_PLUS`
- `X_STEP_MINUS`
- `Y_STEP_PLUS`
- `Y_STEP_MINUS`
- `Z_STEP_UP`
- `Z_STEP_DOWN`

## Safety Gates

- Dry-run is default.
- Real motion requires checking `Enable supervised real motion`.
- Real motion requires typing `SUPERVISED`.
- Real motion also shows a confirmation popup.
- `SAFE_CENTER` retracts Z before XY movement.

## Verification

- GUI file compiled.
- Focused GUI/hardware tests passed: 16 tests.
- Full test suite passed: 147 tests.

## Backup

Edited files are backed up in:

`docs/versions/v0.17.0_ht3_1_hardware_test_console_gui_2026-06-12/backup/`
