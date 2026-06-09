# SPM MK4S Bring-Up Log

Date: 2026-06-09
Operator: SPM / ITU
Printer: Prusa MK4S / MK4-compatible firmware
Serial port: COM5
Firmware: Prusa-Firmware-Buddy 6.2.4

## Passed Tests

- Python virtual environment works
- Required packages installed
- Prusa serial connection works on COM5
- M115 firmware query works
- M114 position readback works
- G28 homing works
- Small Z movement works
- Small X movement works
- Small Y movement works
- Software motion limits block unsafe moves
- Safe center motion works
- Safe square motion works
- Simulated Z driver works
- Safe 3x3 raster scan works
- CSV data logging works
- Plot generation works

## Current Safe Educational Envelope

X: 20 to 80
Y: 20 to 80
Z: 5 to 50

## Created Files

- config/spm_mk4s_config.json
- tools/safe_center_test.py
- tools/safe_square_test.py
- tools/safe_raster_3x3_test.py
- tools/plot_safe_raster.py
- data/safe_raster_3x3_output.csv
- data/safe_raster_3x3_plot.png

## Open Issues

- Arduino/Z-control hardware is not detected
- COM4 is an old FTDI phantom device and should be ignored
- Old tests expect outdated folders and need cleanup later
- core/scan/workflow/spm_workflow.py uses old imports and is not currently usable

## Next Action

Continue with simulated educational SPM workflow first, then reconnect/fix Arduino Z-control later.

## Software Test Update

- Created pytest.ini to restrict active tests to the current tests folder
- Moved outdated tests to tests_legacy
- Added simulated Z driver tests
- Added safe raster CSV output tests
- Current pytest result: 9 passed, 0 failed

## Safe Hardware Demo Update

- Created tools\run_safe_hardware_demo.ps1
- Safe center test: pass
- Safe square test: pass
- Safe 3x3 raster test: pass
- Raster CSV regenerated successfully
- Raster plot regenerated and opened successfully
- Safe hardware demo result: pass

## Raster Module Refactor Update

- Created core\education\safe_raster.py
- Added tests\test_safe_raster_module.py
- Refactored tools\safe_raster_3x3_test.py to use the reusable raster module
- Current pytest result: 11 passed, 0 failed
- Refactored safe raster hardware run: pass


## Config-Based Raster Update

- Created core\education\config_loader.py
- Added tests\test_config_loader.py
- Refactored tools\safe_raster_3x3_test.py to read COM port, limits, and feedrates from config\spm_mk4s_config.json
- Current pytest result: 13 passed, 0 failed
- Config-based safe raster hardware run: pass

## Raster Config Extension Update

- Added safe_raster section to config\spm_mk4s_config.json
- Added get_safe_feedrates and get_safe_raster_config helpers
- Added tests for safe feedrates and raster config
- Refactored tools\safe_raster_3x3_test.py to read raster points, scan Z, simulated signal, and output path from config
- Current pytest result: 15 passed, 0 failed
- Full config-based raster hardware run: pass

## Synthetic Signal Update

- Created core\education\synthetic_signal.py
- Added tests\test_synthetic_signal.py
- Updated safe raster script to use a synthetic non-flat SPM-like signal
- Raster plot now shows different intensities/colors
- Current pytest result: 18 passed, 0 failed

## Synthetic Signal Hardware Demo Verification

- Ran tools\run_safe_hardware_demo.ps1 after synthetic signal integration
- Safe center move: pass
- Safe square move: pass
- Safe 3x3 raster with synthetic signal: pass
- CSV regenerated with non-flat signal values
- Plot regenerated and opened successfully
- Central signal maximum observed at X50 Y50
- Full educational SPM demonstration chain: pass

## Config-Aware Raster Output Test Update

- Updated tests\test_safe_raster_output.py
- CSV row-count test now reads expected raster size from config\spm_mk4s_config.json
- This prepares the project for changing raster size without rewriting tests
- Current pytest result: 18 passed, 0 failed

## Configurable 5x5 Raster Update

- Replaced fixed x_points/y_points with scan_area min/max/resolution config
- Current scan area: X46 to X54, Y46 to Y54, Z20
- Current resolution: 5 x 5
- Generated data\safe_raster_5x5_output.csv
- Updated plot script to read output file from config
- Generated data\safe_raster_5x5_output.png
- 5x5 educational scan map verified visually
- Current pytest result: 18 passed, 0 failed

---

## Final Validated Baseline Update - 2026-06-09

The project has moved beyond the original 3x3 raster test.

Current validated baseline:

- Active pytest suite: 31 passed, 0 failed
- Prusa MK4S connected on COM5
- Safe software check: pass
- Safe hardware demo: pass
- Configured raster scan: 5x5
- Scan-profile validation: active before raster movement
- Synthetic SPM-like signal: active
- CSV output: data\safe_raster_5x5_output.csv
- Plot output: data\safe_raster_5x5_output.png
- Current best backup: C:\SPM_Project_BACKUP_VALIDATED_5X5_HARDWARE_DEMO_2026-06-09.zip

Updated tool names:

- Current raster scan tool: tools\run_configured_raster_scan.py
- Old name no longer used: tools\safe_raster_3x3_test.py

Current scan area:

- X: 46 to 54
- Y: 46 to 54
- Z: 20
- X resolution: 5
- Y resolution: 5
- Total points: 25

Current confirmed central maximum:

- X50 Y50 = 0.9255

The old 3x3 entries above are historical records from the initial bring-up phase.
The current operational baseline is the validated 5x5 scan-profile workflow.
