# SPM_Project

Educational SPM prototype using a Prusa MK4S as a safe motion platform.

## Current Status

- Prusa MK4S connection works on COM5
- Safe educational envelope is configured
- Config-based safe raster scan works
- Simulated Z driver works
- CSV output works
- Plot output works
- Active pytest suite passes: 18 passed, 0 failed

## Safe Educational Envelope

- X: 20 to 80
- Y: 20 to 80
- Z: 5 to 50

## Setup

Use PowerShell:

cd C:\SPM_Project
$env:PYTHONPATH="C:\SPM_Project"

## Safe Software Check

powershell -ExecutionPolicy Bypass -File tools\run_safe_software_check.ps1

## Safe Hardware Demo

Only run when the printer bed/nozzle area is clear:

powershell -ExecutionPolicy Bypass -File tools\run_safe_hardware_demo.ps1

## Main Config

config\spm_mk4s_config.json

## Important Notes

- COM5 is the confirmed Prusa MK4S port.
- COM4 is a phantom FTDI device and should be ignored.
- Arduino/Z-control hardware is not detected yet.
- Legacy tests are preserved in tests_legacy.
- Active tests are controlled by pytest.ini.

## Best Current Backup

C:\SPM_Project_BACKUP_SYNTHETIC_SIGNAL_HARDWARE_VERIFIED_2026-06-09.zip


