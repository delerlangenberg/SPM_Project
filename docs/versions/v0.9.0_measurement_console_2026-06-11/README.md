# Educational SPM v0.9.0 - Measurement Console

Date: 2026-06-11

## Purpose

This version responds to operator feedback from `0830_operator_log.txt`.

## Main Changes

- Added top-level PowerON / PowerOFF / Close workflow:
  - `POWER ON / INITIALIZE` runs the initialization/system-check path.
  - `POWER OFF / SAFE PARK` disables real motion, disconnects dry-run Z, and parks the MK4S.
  - `CLOSE SOFTWARE` remains locked until safe power-off completes.
- Added a dedicated `HARDWARE CHECK` button for no-motion communication and position checks.
- Added a dedicated `MEASUREMENT` window:
  - scan parameter setup
  - MK4S Z / approach training controls
  - scan, pause, stop controls
  - live raster, line, topography, and Z feedback tabs
- Kept hardware tools in a separate window.
- Added single-instance protection so a second Educational SPM interface cannot accidentally open while one is already running.
- Preserved initialize-once behavior: parameter edits after initialization do not require reinitialization.
- Directional raster output records forward, backward, upward, and downward scan samples.

## Backup Notes

The implementation files for this version are the project files in:

- `core/application/gui_scan_launcher.py`
- `core/application/workstation_status.py`
- `core/education/safe_raster.py`
- `core/acquisition/raster_stream.py`
- `tools/run_configured_raster_scan.py`

The full test suite passed after this version:

- `110 passed`

Backup copies are stored in:

- `docs/versions/v0.9.0_measurement_console_2026-06-11/backup/`

## Operator Feedback Addressed

1. Prevent multiple Educational SPM windows.
2. Make PowerON, PowerOFF, and Close the main session controls.
3. Add a hardware check button below the power controls.
4. Use a Measurement window for scan setup, Z approach, scan/pause/stop, and live four-direction feedback.
5. Keep hardware testing separate from normal measurement.
6. Keep the project versioned with a version README.
