# Phase 2.3B Non-Blocking GUI Windows and Measurement Workflow Shell

## Purpose

This phase establishes the agreed GUI architecture before connecting more hardware logic.

The main operator page must stay light. Complex views open as normal software windows and do not block the main page.

## Menu structure

### View

- Line Mode
- Topography
- Live View
- System Status

### Tools

- Academic AI Assistant
- Check Scan Profile
- Reset Raster

### Open

- Scan Setup
- Line Mode
- Topography

### About

- About Project

## Non-blocking windows

Windows are not modal overlays. They can remain open while the operator continues to use the main page.

Implemented windows:

- Scan Setup Window
- Line Mode - Directional Line Scans
- Topography - Directional Accumulation
- Live View / Measurement Window
- System Status Window
- Academic AI Assistant
- About Window

## Measurement workflow shell

The main page now contains a Measurement Control panel:

1. Default Center
2. Measurement Start
3. Pause
4. Stop

The intended experiment logic is:

1. connect / ON,
2. set default center,
3. approach with Z scanner,
4. start measurement,
5. scan one X line,
6. step Y,
7. repeat line by line,
8. accumulate topography,
9. pause/stop/export later.

## Code split

- `app.js`
  - light main shell
  - status
  - AI
  - button routing

- `window_manager.js`
  - non-blocking windows
  - dropdown window opening
  - draggable windows

- `scan_raster.js`
  - scan profile
  - measurement start/pause/stop
  - line scan drawing
  - topography drawing

- `core/web/spm_scan_simulation.py`
  - backend simulation-only scan model

## Next phase

Phase 2.4 should connect this GUI shell to existing working project modules in small independent steps:

- Z approach/readback module
- XY default center module
- dry-run raster executor module
- live output/export module
