# Phase 2.3A Modular Scan Measurement Repair

## Purpose

This phase repairs the browser-side split so scan measurement code is not mixed into the main GUI code.

This is not the final locked scan model. It is the first modular scan-measurement workspace.

## Correct project direction

The web GUI should stay lightweight.

The main page only handles:

- menu/window opening
- basic status
- operator log
- first-level controls

Each complex function should live in its own code file:

- `app.js`
  - main GUI shell
  - status loading
  - menu/window handling
  - button routing

- `scan_raster.js`
  - scan setup actions
  - one-line scan action
  - raster simulation loop
  - topography drawing

- future `z_approach.js`
  - Z approach/retract/readback UI logic

- future `hardware_control.js`
  - safe hardware command integration

- future `ai_assistant.js`
  - Academic AI advisory UI logic

## SPM scan principle for this module

The scan measurement module represents this workflow:

1. maintain fixed Z setpoint / distance,
2. scan one X line,
3. use Z feedback as the measured topography signal,
4. step one increment in Y,
5. repeat line by line,
6. accumulate all lines into a 2D topography window.

## Important design rule

Do not overcrowd the main page.

Scan windows should be opened from View/Open/scan controls.
Only essential status and logs stay visible on the main page.
