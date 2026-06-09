# SPM PC Handoff

## Current Stable Baseline

Project folder:

C:\SPM_Project

Current best backup:

C:\SPM_Project_BACKUP_VALIDATED_5X5_HARDWARE_DEMO_2026-06-09.zip

## Current State

- Hostname: OBSERVATORY
- Project folder: C:\SPM_Project
- Virtual environment: C:\SPM_Project\.venv
- Prusa MK4S port: COM5
- COM4 is a phantom FTDI device and should be ignored
- Arduino/Z-control hardware is not detected yet

## Safe Educational Motion Envelope

Configured in:

config\spm_mk4s_config.json

Limits:

- X: 20 to 80
- Y: 20 to 80
- Z: 5 to 50

Current scan area:

- X: 46 to 54
- Y: 46 to 54
- Z: 20
- X resolution: 5
- Y resolution: 5
- Total raster points: 25

## Current Confirmed Working Chain

Prusa MK4S motion platform
-> scan-profile validation
-> configurable 5x5 raster scan
-> synthetic SPM-like signal
-> CSV output
-> colored scan map

## Passed

- Active pytest suite: 31 passed, 0 failed
- Prusa serial connection works on COM5
- M115 firmware query works
- M114 position query works
- Software limits block unsafe movement
- Safe center test works
- Safe square test works
- Validated configured 5x5 raster scan works
- Scan profile validation runs before raster movement
- Synthetic SPM-like signal works
- CSV output works
- Plot output works
- Safe software check works
- Safe hardware demo works

## Important Files

Configuration:

config\spm_mk4s_config.json

Core modules:

core\education\safe_raster.py
core\education\config_loader.py
core\education\synthetic_signal.py
core\education\scan_profile.py
core\motion\prusa_gcode_backend.py
core\z_control\z_driver_simulated.py

Tools:

tools\run_configured_raster_scan.py
tools\plot_safe_raster.py
tools\run_safe_software_check.ps1
tools\run_safe_hardware_demo.ps1
tools\prusa_ping.py
tools\safe_center_test.py
tools\safe_square_test.py

Tests:

tests\test_scan_profile.py
tests\test_safe_raster_module.py
tests\test_safe_raster_output.py
tests\test_config_loader.py
tests\test_synthetic_signal.py
tests\test_simulated_z_driver.py
tests\motion\test_prusa_backend.py
tests\motion\test_prusa_connect.py

## Run Setup First

cd C:\SPM_Project
$env:PYTHONPATH="C:\SPM_Project"

## Run Tests

.\.venv\Scripts\python.exe -m pytest -v

Expected result:

31 passed

## Safe Software Check

Run from PowerShell:

powershell -ExecutionPolicy Bypass -File tools\run_safe_software_check.ps1

This performs:

- pytest
- Prusa no-motion ping
- M115 firmware query
- M114 position query
- raster plot regeneration

This does not run the raster scan.

## Safe Hardware Demo

Run only when the printer bed/nozzle/probe area is clear:

powershell -ExecutionPolicy Bypass -File tools\run_safe_hardware_demo.ps1

This performs:

- safe center move
- safe square move
- validated configured 5x5 raster scan
- CSV regeneration
- plot regeneration
- plot opening

## Current Output Files

CSV:

data\safe_raster_5x5_output.csv

Plot:

data\safe_raster_5x5_output.png

Current confirmed central maximum:

X50 Y50 = 0.9255

## Current Safety Principle

Never let application/user settings move outside motion_limits.

The current raster script validates the scan profile before connecting movement commands to the Prusa.

The application layer should use scan_profile.py before any future GUI, contact probe, AFM, or STM mode.

## Open Issues

- Arduino/Z-control hardware is not detected yet
- COM4 is a phantom FTDI device and should be ignored
- Real probe hardware is not integrated yet
- Current signal is synthetic educational signal, not real AFM/STM physics
- PyQt/live GUI not built yet

## Next Recommended Step

Build the first application layer around the validated backend.

Recommended order:

1. Add scan mode enum/config handling:
   - SIMULATED_SURFACE
   - CONTACT_PROBE
   - AFM_CONTACT
   - STM_DEMO

2. Add a simple CLI scan launcher.

3. Add PyQt5/pyqtgraph live plot later.

4. Add real probe approach/retract workflow only after mechanics are mounted and tested.

---

## CLI Application Layer Added

The first application layer has been added.

New files:

- core\application\cli_scan_launcher.py
- core\application\__init__.py
- tests\test_cli_scan_launcher.py
- tools\run_cli_dry_run.ps1

Current CLI dry-run command:

powershell -ExecutionPolicy Bypass -File tools\run_cli_dry_run.ps1

Direct command:

.\.venv\Scripts\python.exe core\application\cli_scan_launcher.py --dry-run

The CLI launcher currently:

- loads config
- builds scan profile
- builds motion limits
- validates scan profile
- prints output file
- exits without movement in dry-run mode

Current pytest result after CLI layer:

33 passed, 0 failed

The safe software check now includes the CLI dry run.

---

## CLI Hardware Execution Verified

The CLI application layer can now execute the verified hardware raster scan only when explicitly requested.

Command:

.\.venv\Scripts\python.exe core\application\cli_scan_launcher.py --execute-hardware

Confirmed result:

- scan profile validation: PASS
- hardware execution requested explicitly
- verified configured 5x5 raster scan ran successfully
- CSV saved: data\safe_raster_5x5_output.csv
- hardware disconnected cleanly

Default CLI behavior remains safe:

.\.venv\Scripts\python.exe core\application\cli_scan_launcher.py

This validates the profile but does not move hardware.

---

## CLI Scan Parameter Overrides Added

The CLI application layer now supports user-overridable scan parameters:

- --x-min
- --x-max
- --y-min
- --y-max
- --z
- --x-resolution
- --y-resolution

Safe dry-run example:

.\.venv\Scripts\python.exe core\application\cli_scan_launcher.py --dry-run --x-min 48 --x-max 52 --y-min 48 --y-max 52 --z 20 --x-resolution 3 --y-resolution 3

Confirmed result:

- validation: PASS
- no hardware movement
- profile updated from CLI arguments

Unsafe example:

.\.venv\Scripts\python.exe core\application\cli_scan_launcher.py --dry-run --x-min 10 --x-max 52

Confirmed result:

- validation: FAIL
- reason: x_min is outside motion limits
- no Python traceback shown
- no hardware movement

Current pytest result:

37 passed, 0 failed

---

## CLI Interface Hardware Overrides Verified

The CLI application layer now forwards validated scan parameters to the hardware raster script.

Verified interface command with 3x3 override:

.\.venv\Scripts\python.exe core\application\cli_scan_launcher.py --execute-hardware --x-min 48 --x-max 52 --y-min 48 --y-max 52 --z 20 --x-resolution 3 --y-resolution 3

Confirmed result:

- CLI validation: PASS
- hardware execution requested explicitly
- raster script received the CLI profile
- 3x3 hardware raster completed successfully
- CSV saved
- hardware disconnected cleanly

The default 5x5 scan was then restored by running:

.\.venv\Scripts\python.exe core\application\cli_scan_launcher.py --execute-hardware

Current pytest result:

37 passed, 0 failed

Current best backup:

C:\SPM_Project_BACKUP_CLI_INTERFACE_HARDWARE_OVERRIDES_2026-06-09.zip

---

## Interface Output File Safety Added

The CLI interface and raster script now support a separate output file argument.

New CLI argument:

--output-file

Example 3x3 interface hardware test without overwriting the 5x5 baseline:

.\.venv\Scripts\python.exe core\application\cli_scan_launcher.py --execute-hardware --x-min 48 --x-max 52 --y-min 48 --y-max 52 --z 20 --x-resolution 3 --y-resolution 3 --output-file data/interface_test_output.csv

Confirmed result:

- data\interface_test_output.csv has 9 rows
- data\safe_raster_5x5_output.csv remains 25 rows
- baseline tests remain clean

Current pytest result:

37 passed, 0 failed

Current best backup:

C:\SPM_Project_BACKUP_INTERFACE_OUTPUT_FILE_SAFE_2026-06-09.zip

---

## Separate Interface Plot Output Added

The plotting script now supports:

- --input-file
- --output-file
- --cmap

Default 5x5 plot command:

.\.venv\Scripts\python.exe tools\plot_safe_raster.py

Separate interface test plot command:

.\.venv\Scripts\python.exe tools\plot_safe_raster.py --input-file data\interface_test_output.csv --output-file data\interface_test_output.png --cmap plasma

Confirmed outputs:

- data\safe_raster_5x5_output.png
- data\interface_test_output.png

Current pytest result:

37 passed, 0 failed

Current best backup:

C:\SPM_Project_BACKUP_INTERFACE_SEPARATE_PLOT_2026-06-09.zip
