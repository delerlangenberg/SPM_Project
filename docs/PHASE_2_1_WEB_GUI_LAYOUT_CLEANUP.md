# Phase 2.1 Professional Web GUI Layout Cleanup

## Purpose

This phase converts the Phase 2.0 browser console into a cleaner professional operator workspace.

The visible page should not be a roadmap page. The roadmap belongs in documentation and API metadata. The main operator screen should show only the controls needed for first contact with the machine.

## Main page

The main page now contains:

- Main System
  - ON
  - OFF
  - STATUS
  - CLOSE
  - connection port
  - operating mode

- Z Scanner
  - Approach
  - Retract
  - Read Z
  - Park Z
  - Z step
  - safe Z range

- XY Jog Control
  - X-
  - X+
  - Y-
  - Y+
  - Center
  - Open Scan Setup
  - Open Live View

- Status / Live Log
  - MK4S status
  - Z scanner status
  - XY scanner status
  - operator log

## Floating windows

The top menu and selected buttons open floating windows:

- View → Live View / Measurement Window
- Tools / Open → Scan Setup Window
- STATUS → System Status Window
- About → About Window

## Integration plan

The next phases should inject working code from older project versions into these windows and controls:

- Phase 2.2: system ON/OFF/STATUS/CLOSE integration
- Phase 2.3: Z approach/retract/readback integration
- Phase 2.4: XY scan setup, preview scan, scan execution, export
- Phase 2.5: live plot, CSV/PNG/Gwyddion export
