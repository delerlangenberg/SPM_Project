# Educational SPM v0.10.1 - Step 1 Clear Workstation Windows

Date: 2026-06-11

## Why This Step Exists

The latest operator feedback said the main workspace was still too busy and the window names were not clear enough. This step starts a controlled roadmap: finish one visible change, show it, get operator approval, then move to the next step.

## Step 1 Completed

- Renamed the application frame to: `Educational SPM v0.10.1 - Operator Workspace - Prusa MK4S`.
- Renamed the active phase to: `Step 1 - Clear workstation windows`.
- Renamed the main workflow buttons:
  - `MEASUREMENT SETUP`
  - `XY SCANNER`
  - `Z REGULATION`
  - `HARDWARE CHECK`
- Removed the four direction image launcher buttons from the main workspace.
- Combined the hardware entry point into one main `HARDWARE CHECK` window button.
- Added `RUN HARDWARE CHECK` inside the hardware window.

## Roadmap

### Step 1 - Clear Workstation Windows

Make the main workspace fit the monitor and show only the major operator windows.

### Step 2 - Measurement Window Redesign

Replace the current measurement console with a clean measurement window:

- Top section: line-scan view.
- Bottom section: topography view.
- Each section can switch between forward, backward, upward, and downward scan directions.
- Keep scan setup, scan mode, scan area, scan/start/pause/stop in one logical measurement flow.

### Step 3 - Z Regulation / Approach Window

Build the Z regulation window as the next active engineering focus:

- Show live Z position.
- Show approach animation/status.
- Separate dry-run training from real Z movement.
- Prepare for constant-height feedback control.

### Step 4 - Initialize Once Workflow

Make `POWER ON / INITIALIZE` perform the full readiness sequence once:

- Check MK4S communication.
- Load scan-mode defaults.
- Confirm limits and safe state.
- Keep the system initialized while the operator changes scan parameters.

### Step 5 - Real Measurement Flow

Make the user workflow simple:

1. Select demo or real mode.
2. Select scan mode/profile.
3. Configure XY scan range.
4. Approach Z.
5. Scan, pause, stop, save.
6. Safe park Z, then XY, then close.

## Backup

The edited files for this checkpoint are backed up in:

`docs/versions/v0.10.1_clear_workstation_windows_2026-06-11/backup/`
