# Phase Separation Correction

Created: 2026-06-18 19:06:46

Correction:
The previous Phase 2.2 work mixed two different layers:
1. Z-scanner control and Z live feedback.
2. XY raster scan measurement planning.

Correct phase structure:

## Phase 2.2 - Z Scanner Control and Live Feedback

Scope:
- Z position readout.
- Z range display.
- Surface Z setting.
- Clearance above surface in micrometers.
- Fast approach distance.
- Fine Z step size.
- Z resolution display.
- Live Z feedback window.
- Software-position Z approach.
- Safe retract.
- No XY raster scan execution.

Purpose:
Prepare the vertical scanner behavior before real point measurement.

## Phase 2.3 - XY Scan Measurement and Raster Imaging

Scope:
- X/Y scan area.
- X/Y resolution.
- Pixel pitch.
- X+ and X- trace/retrace.
- Y+ and Y- trace/retrace.
- Line accumulation.
- Topography image building.
- Scan-time estimation.
- CSV/image output.

Purpose:
Build the real scan measurement workflow after the Z scanner is understood.

Decision:
The scan planner and raster preview code already created will be treated as
Phase 2.3 staging. It should not be active in the Phase 2.2 UI.
