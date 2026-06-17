# MK4S Machine Limits and Hardware Test - 2026-06-11

## No-Motion Machine Information Query

Tool:

- `tools/query_mk4s_machine_limits.py`

The query uses no-motion G-code/status commands:

- `M115` firmware info
- `M114` current position
- `M119` endstop status
- `M503` firmware settings
- `M211` software endstops

## Firmware / Controller

- Port: COM5
- Firmware: Prusa-Firmware-Buddy 6.2.4+8909
- Machine type reported: Prusa-MK4

## Firmware-Reported Software Endstops

From `M211`:

- X min: -1.00
- X max: 251.00
- Y min: -4.00
- Y max: 211.00
- Z min: 0.00
- Z max: 221.00

These are the MK4S firmware soft limits, not the SPM operating envelope.

## Current SPM Safety Envelope

Configured in `config/spm_mk4s_config.json`:

- X: 20 to 80
- Y: 20 to 80
- Z: 5 to 50

Current validated scan:

- X: 46 to 54
- Y: 46 to 54
- Z: 20
- Resolution: 5 x 5

## Hardware Test Result

Command:

- `powershell -ExecutionPolicy Bypass -File tools/run_safe_hardware_demo.ps1`

Completed successfully:

- Safe center move: PASS
- Safe square move: PASS
- Validated 5 x 5 raster scan: PASS
- CSV saved: `data/safe_raster_5x5_output.csv`
- Metadata saved: `data/safe_raster_5x5_output.metadata.json`
- Plot regenerated: `data/safe_raster_5x5_output.png`

Observed raster maximum:

- X50 Y50 = 0.9255 simulated signal

## Software Regression Fixed

During the hardware demo, the raster scan completed but plot regeneration initially failed because `tools/plot_safe_raster.py` required explicit `--input-file` and `--output-file`.

Fix:

- Restored safe 5 x 5 default input/output paths.
- Kept explicit arguments and legacy `--cmap` support.

Verification:

- Active test suite: 88 passed.

## 2026-06-11 Sequential 3 x 3 Hardware Test

Purpose:

- Start the staged hardware test sequence with the smallest useful raster.
- Confirm hardware communication, safe limits, movement, CSV, metadata, plot, and readback before larger scans.

Pre-checks:

- No-motion hardware communication: PASS
- No-motion MK4S limits/current-position query: PASS

Firmware soft limits remembered:

- X: -1.00 to 251.00
- Y: -4.00 to 211.00
- Z: 0.00 to 221.00

SPM-safe envelope retained:

- X: 20 to 80
- Y: 20 to 80
- Z: 5 to 50

3 x 3 hardware raster command:

- `python core/application/cli_scan_launcher.py --execute-hardware --x-min 48 --x-max 52 --y-min 48 --y-max 52 --z 20 --x-resolution 3 --y-resolution 3 --output-file data/hardware_3x3_check_2026_06_11.csv`

3 x 3 hardware raster result:

- Movement range: X 48 to 52, Y 48 to 52, Z 20
- Resolution: 3 x 3
- Raster points: 9
- CSV: `data/hardware_3x3_check_2026_06_11.csv`
- Metadata: `data/hardware_3x3_check_2026_06_11.metadata.json`
- Plot: `data/hardware_3x3_check_2026_06_11.png`
- Result: PASS

Observed signal:

- Minimum: 0.2890
- Maximum: 0.9255
- Center signal: X50 Y50 = 0.9255

Next staged hardware test:

- 5 x 5 within X 46 to 54, Y 46 to 54, Z 20 after visual inspection of the 3 x 3 result.

## 2026-06-11 SPM-Safe Axis Min/Max Motor Check

Purpose:

- Move each MK4S axis one by one to the current SPM-safe minimum and maximum.
- Record the actual position readback after each move.
- Return to the safe center position after the check.

Important:

- This test did not move to full MK4S firmware soft-endstop extremes.
- It moved only inside the configured SPM-safe envelope.

Tested SPM-safe movement range:

- X min: 20.00, X max: 80.00
- Y min: 20.00, Y max: 80.00
- Z min: 5.00, Z max: 50.00

Final returned position:

- X: 50.00
- Y: 50.00
- Z: 20.00

Result:

- X min/max: PASS
- Y min/max: PASS
- Z min/max: PASS

Output:

- `data/axis_limit_check_2026_06_11.csv`

Recorded readback:

```text
x_min -> X20 Y50 Z20
x_max -> X80 Y50 Z20
y_min -> X50 Y20 Z20
y_max -> X50 Y80 Z20
z_min -> X50 Y50 Z5
z_max -> X50 Y50 Z50
return -> X50 Y50 Z20
```

Verification:

- Active test suite after axis check: 94 passed.

## 2026-06-11 Official MK4S Maximum Position Test

Source:

- Official Prusa MK4S product page reports build volume: 250 x 210 x 220 mm.
- Official Prusa MK4S/MK3.9S handbook v1.01, Product Information page, reports build volume: 250 x 210 x 220 mm.

Purpose:

- Test the official maximum positions from the Prusa build volume.
- Record actual position readback for X, Y, and Z maxima.
- Return to SPM-safe center after the test.

Important:

- Z minimum 0 was not automatically tested because it is collision-sensitive.
- This test verifies maximum travel only:
  - X max 250
  - Y max 210
  - Z max 220

Test sequence:

- Start: X50 Y50 Z20
- Raise to Z50 for XY clearance
- Move X to 250, then return X to 50
- Move Y to 210, then return Y to 50
- Move Z to 220, then return Z to 20

Result:

- X official max 250: PASS
- Y official max 210: PASS
- Z official max 220: PASS
- Final returned position: X50 Y50 Z20

Output:

- `data/original_mk4s_max_check_2026_06_11.csv`

Recorded readback:

```text
x_official_max -> X250 Y50 Z50
y_official_max -> X50 Y210 Z50
z_official_max -> X50 Y50 Z220
return -> X50 Y50 Z20
```

## 2026-06-11 Official MK4S X/Y Minimum Position Test

Purpose:

- Complete the X/Y original-parameter movement record.
- Test official X/Y minimum positions at raised Z clearance.
- Return to X50 Y50 Z20.

Important:

- Z0 was still not automatically tested because it is collision-sensitive.

Test sequence:

- Start: X50 Y50 Z20
- Raise to Z50 for XY clearance
- Move X to 0, then return X to 50
- Move Y to 0, then return to X50 Y50 Z20

Result:

- X official min 0: PASS
- Y official min 0: PASS
- Final returned position: X50 Y50 Z20

Output:

- `data/original_mk4s_xy_min_check_2026_06_11.csv`

Recorded readback:

```text
x_official_min -> X0 Y50 Z50
y_official_min -> X50 Y0 Z50
return -> X50 Y50 Z20
```

## Software Parameter Update

The project configuration now separates machine capability from routine SPM safety guidance:

- `motion_limits`: official MK4S machine range, X 0..250, Y 0..210, Z 0..220
- `spm_safe_limits`: recommended routine SPM range, X 20..80, Y 20..80, Z 5..50
- `parking_position`: workstation shutdown position, X 1, Y 1, Z 100

The GUI scan-mode popup now shows:

- Official MK4S build volume from the manual
- Tested machine extrema
- Recommended SPM-safe routine range

The GUI also includes a `PARK MK4S` action and close-protection behavior:

- Parking retracts Z to 100 first.
- After Z clearance is reached, XY moves to X1 Y1.
- If the workstation has been initialized, closing the GUI attempts this park sequence before the interface exits.
- If parking fails, the GUI remains open so the operator can recover safely.
