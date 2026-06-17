# Educational SPM v0.11.0 - Step 2 Live SPM Raster Measurement

Date: 2026-06-11

## Purpose

This step turns the Measurement window into a real SPM-style live measurement view instead of a collection of static summaries.

## Operator Model

The intended measurement sequence is:

1. Z scanner approaches the sample and regulates to the selected setpoint distance/signal.
2. The scanner sweeps in X to produce a forward line.
3. The scanner sweeps back in X to produce a backward line.
4. The scanner steps in Y and repeats the X forward/backward pair.
5. The full Y pass accumulates into the topography image.
6. The raster can return in the opposite Y direction for the return pass.
7. After measurement, Z retracts and XY is parked by the safe shutdown sequence.

## Completed In This Step

- Version bumped to `v0.11.0`.
- Measurement window now opens automatically after the main workspace launches.
- Measurement window now has two main scientific views:
  - Top: live line scan for the current X sweep.
  - Bottom: accumulated topography from raster lines.
- Added direction selectors:
  - Line view: current, forward, backward.
  - Topography view: current, upward, downward, all.
- Added a low-CPU `QTimer` live raster engine for demo mode.
- Demo `SCAN` now runs the live regulated raster view instead of only waiting for a blocking dry-run command.
- Live demo scan writes a CSV compatible with the existing plot/export path.
- Hardware communication check was run safely with no motion and passed on COM5.
- A full safe demo raster was generated at:
  - `data/v0_11_full_demo_raster.csv`
  - `data/v0_11_full_demo_raster.png`

## Hardware Test Result

Safe no-motion hardware communication check:

- Overall: PASS
- MK4S detected on COM5 at 115200 baud.
- Firmware readback succeeded.
- Position readback succeeded: X 1.00, Y 1.00, Z 100.00.
- Fine Z scanner remains a future subsystem; current Z approach controls are training/dry-run until the fine Z hardware is installed.

## Next Step

Step 3 should focus on Z Regulation / Approach:

- Make the Z Regulation window show approach animation.
- Show current Z position and setpoint.
- Separate dry-run Z simulation from future real fine-Z scanner commands.
- Prepare the constant-height feedback loop that will later drive real topography.

## Backup

Edited files are backed up in:

`docs/versions/v0.11.0_live_spm_raster_measurement_2026-06-11/backup/`
