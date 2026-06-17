# Phase 2.3 SPM Raster Scan Model

## Purpose

This phase implements the web console model for scanning probe microscopy raster scanning.

The physical principle is:

1. The probe approaches the surface.
2. A fixed Z distance/setpoint is maintained.
3. During one X line scan, the Z feedback follows the sample surface.
4. The recorded Z feedback line becomes one topography line.
5. The scanner moves one Y step.
6. The next X line is scanned.
7. All X lines are accumulated into a 2D topography image.

## Web GUI windows

Phase 2.3 adds:

- Scan Setup Window
  - X min/max
  - Y min/max
  - X points
  - Y lines
  - Z setpoint
  - surface simulation model

- Line Scan Window
  - current X line
  - Z feedback signal

- Accumulated Topography Window
  - topography image built line by line

- Live View Window
  - current line scan
  - accumulated topography

## API endpoints

- `/api/scan/profile`
- `/api/scan/line`

## Safety

This phase is simulation-only.

No real MK4S motion is executed.

The next phase should connect this model to existing safe local hardware modules:

- profile validation
- Z approach/readback
- XY raster execution
- output CSV/PNG/Gwyddion export
