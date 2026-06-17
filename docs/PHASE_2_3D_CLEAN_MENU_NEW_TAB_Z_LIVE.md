# Phase 2.3D Clean Menu Logic and Default New-Tab Views

## Purpose

This phase cleans the professional GUI architecture after testing Phase 2.3C.

## Final menu rule

### View

Measurement and monitoring views only. These open in new browser tabs by default for two-monitor operation.

- Line Mode
- Topography
- Z Feedback Live View
- System Status

### Tools

Tools only. No duplicate view items.

- Academic AI Assistant
- Check Scan Profile
- Reset Raster

### Open

Open/load/configuration items only. No duplicate view items.

- Scan Setup

### About

Project information only.

- About Project

## Popup blocker rule

View/Open/About window entries use normal browser links:

- `href="/?window=...&standalone=1"`
- `target="_blank"`
- `rel="noopener noreferrer"`

This avoids relying on JavaScript `window.open()` and should behave better with popup blockers.

## View responsibility

- Z Feedback Live View: Z feedback / fixed-distance monitoring only.
- Line Mode: X+/X-/Y+/Y- line scans.
- Topography: four directional accumulated surface views.

## Code split

- `window_manager.js`: dropdowns, standalone tab mode, local floating window handling.
- `scan_raster.js`: measurement start/pause/stop, line mode, topography.
- `z_live.js`: Z feedback live view.
- `app.js`: main status, AI routing, first-level button handling.
