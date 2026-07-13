# SPM Operator Software User Guide

Version: v0.2.5

This guide covers the desktop operator software for the SPM Prusa scanner.

## Launch

```powershell
cd D:\SPM_Prusa_Project
.\spm.bat
```

The launcher enables the current hardware gates used by the operator workstation:

- `SPM_WEB_ALLOW_READONLY_HARDWARE=1`
- `SPM_WEB_ALLOW_HEALTH_MOTION=1`
- `SPM_WEB_ALLOW_REAL_SCAN=1`
- `SPM_WEB_ALLOW_FOIL_TAP=1`

Only use this launcher when the surface is clear, the scanner is watched, and Phase 2.1 diagnosis has passed.

## Academic AI

Academic AI is advisory-only. It can explain logs, suggest next checks, and help diagnose operator workflow issues, but it cannot execute machine motion.

The software uses Academic AI 3.0 through:

```text
https://it-u-api.academic-ai.at/api/v1/llm/chat
```

Default model:

```text
GPT-5.2
```

Credentials are read in this order:

1. `ACADEMIC_AI_CLIENT_ID` and `ACADEMIC_AI_CLIENT_SECRET`
2. `CLIENT_ID` and `CLIENT_SECRET`
3. Local development fallback: `docs/API_SPM.txt`

Optional overrides:

```powershell
$env:ACADEMIC_AI_MODEL='GPT-5.2'
$env:ACADEMIC_AI_MAX_TOKENS='700'
$env:ACADEMIC_AI_TIMEOUT_SECONDS='30'
```

Disable local credential-file fallback:

```powershell
$env:ACADEMIC_AI_DISABLE_LOCAL_FILE='1'
```

## Normal Operator Flow

1. Open the software.
2. In Phase 2.1 System Control, select the port and connect read-only.
3. Run Diagnosis. This verifies position readback and, when enabled, performs visible XYZ health motion.
4. Use Safe Standby when recovery or a known safe default position is needed.
5. In Phase 2.2 Z Scanner, read Z and apply a target Z setpoint.
6. Open Phase 2.3 Measurement Control if it is not already visible.
7. Use Start Simulation first to verify scan geometry and signal windows.
8. Use Start Real Scan only after the scan area and Z height are physically safe.

## Real Scan Mode

The first real scan mode is a constant-Z raster with live `M114` readback:

- Moves to the configured Z setpoint.
- Moves XY point by point through the configured raster.
- Reads real X/Y/Z after each point.
- Streams each point into the live Z trace, line mode, and topography windows.
- Stops at command boundaries when Stop or STOP Z is pressed.

Default measurement setup:

- X range: 100 mm
- Y range: 100 mm
- X points: 10
- Y lines: 1

This gives a first real line scan across a 100 mm field. Increase Y lines only after the line-mode hardware behavior is trusted.

## Closing The Software

Closing the main window or using File > Exit is a safe-shutdown operation.

The software automatically:

1. Requests any active scan/Z sequence to stop at the next command boundary.
2. Moves the hardware to Safe Standby: X125 Y105 Z120.
3. Disconnects the software state.
4. Allows the window to close only after the safe sequence succeeds.

A modal progress window is shown because this can take several seconds. If Safe Standby fails, the software stays open so the operator can recover manually.

## Matching Real Hardware Path To Simulation

For real hardware to follow the same XY path as the simulated gold/atom surface, set:

- X range mm
- Y range mm
- X points
- Y lines
- Scan speed mm/s
- Z setpoint mm
- `SPM_WEB_ALLOW_REAL_SCAN=1`

The current real scan is constant-Z raster plus `M114` readback. The selected simulation surface changes the simulated signal only; it does not yet command Z height modulation. To physically replay a gold-atom height map, the next controlled mode must add a gated Z-topography replay with amplitude scale, maximum Z delta per point, and sensor feedback limits.

## Foil-On-Foam Z Feedback Test

Goal: prove that each XY point can produce its own Z feedback value before building full tapping-mode raster.

Recommended hardware setup:

- Put foam on the bed.
- Put aluminum foil on top of the foam.
- Place the test area near the center of the scanner.
- Start from Safe Standby and a known high Z.

Stage 1 - stationary tap:

1. Move to center XY.
2. Set a high safe start Z.
3. Descend in small Z steps.
4. After each step, read the contact/load-cell/probe state.
5. Record the first Z where contact is detected.
6. Retract by a configured lift distance.
7. Repeat 5-10 times at the same XY.

Pass condition:

- Contact Z repeats within a small tolerance.
- Retraction clears contact every time.
- STOP and Safe Shutdown still work.

Stage 2 - line tapping:

1. Use 5-10 X points across a short line.
2. At each X point, perform the same tap cycle.
3. Store `contact_z_mm` as the line signal.
4. Plot `contact_z_mm` live in the line window.

Stage 3 - tapping topography:

1. Extend line tapping to multiple Y lines.
2. Store each point as `x`, `y`, `contact_z_mm`, `contact_state`, `tap_count`, and `retract_z_mm`.
3. Render topography from `contact_z_mm`.

Required software parameters for tapping mode:

- `tap_start_z_mm`
- `tap_min_z_mm`
- `tap_step_fast_mm`
- `tap_step_fine_mm`
- `contact_confirm_reads`
- `contact_source` such as `M119`, load-cell API, or external sensor channel
- `retract_after_tap_mm`
- `max_tap_attempts`
- `max_contact_z_jump_mm`
- `xy_points`
- `y_lines`

This is the correct bridge from constant-Z position raster to real SPM-style feedback. The signal becomes the measured contact/feedback Z at each XY point, not the commanded Z.

## Foil Tap 50x50 Preset

The Measurement Control window includes `Foil Tap 50x50`.

This preset sets:

- X range: 50 mm
- Y range: 50 mm
- X points: 10
- Y lines: 10
- Center: X125 Y105

The current experimental implementation uses `M119 z_min` as the contact source and is therefore a contact-channel test, not yet a certified feedback loop. Start the hardware-enabled software with:

```powershell
cd D:\SPM_Prusa_Project
.\spm.bat
```

Recommended first settings for the 8 mm foam with foil:

- Tap start Z: 150 mm
- Tap min Z: 120 mm
- Tap retract: 3 mm

Watch the first points carefully. If no contact is detected before Tap min Z, the point is recorded as no-contact and the scan should be stopped and the contact source reviewed.

By default, the software aborts the foil tap scan at the first no-contact point. This is intentional for the first hardware validation.

## Safety Notes

- Real scan is not a contact-detection SPM feedback loop yet.
- The current real scan records actual position readback as the signal.
- Sensor-based auto approach remains simulation-first until the sensor backend is verified.
- AI advice must always be reviewed by the operator before any physical action.
