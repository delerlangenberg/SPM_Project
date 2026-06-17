# Phase 2.0 Web-Based SPM Prusa Operator Console

## Purpose

This phase creates a browser-based main operator console for the Educational SPM Prusa MK4S project.

The goal is to move away from a crowded PyQt-only workflow and create a clearer browser interface that can later receive the proven working parts from old project versions.

## Main window structure

### Top menu

- View
- Tools
- Open
- About

### Main System column — Phase 2.1

- ON
- OFF
- STATUS
- CLOSE
- connection port
- dry-run / real-motion mode selector

### Z Scanner column — Phase 2.2

- Approach
- Retract
- Read Z
- Park Z
- Z step size
- safe Z min/max
- approach strategy selector

### XY Scanner column — Phase 2.3

- X-
- X+
- Y-
- Y+
- Center
- X/Y scan limits
- X/Y scan resolution
- feedrate
- output file
- preview scan
- start scan
- stop scan
- export

### Live View / Measurement — Phase 2.4

- live scan preview placeholder
- operator log
- future CSV/PNG/Gwyddion export integration

### Professional workflow — Phase 2.5

- connect
- initialize
- approach
- preview
- scan
- export
- park
- shutdown

## Implementation notes

The Phase 2.0 server intentionally uses only the Python standard library. This avoids dependency problems and gives the project a stable web UI shell.

The current API endpoints are stubs:

- `/api/status`
- `/api/phase-map`

Future phases will connect these endpoints to the existing MK4S, Z, XY, scan, and hardware-status modules.
