# Phase 2.2C.0 Professional UI Architecture Lock

Date: 2026-06-18

Project:
D:\SPM_Prusa_Project

Purpose:
Prepare the SPM Prusa MK4S operator console for a professional cockpit-style UI.

Required main UI sections:

1. Main System - Phase 2.1
- Hardware/API status
- Read-only connection state
- Health/safe controls
- Safe retract
- No homing
- No heating
- No uncontrolled motion

2. Z-Scanner / Feedback - Phase 2.2
- Current Z mm
- Count Z
- Z resolution: 2.5 micrometers/count
- Declared surface Z
- Clearance above surface in micrometers
- Computed target Z
- Rounded executable target Z
- Fast guard distance
- Fine Z step size
- Retract Z
- Live Z feedback
- Software-position Z approach only
- No contact claim from M119

3. Measurement - Phase 2.3
- Measurement cockpit must include all information currently split across:
  - XY jog control window
  - Measurement control window
- This section may be visible as Phase 2.3 staging.
- It must not activate uncontrolled XY raster scan during Phase 2.2.

4. SPM Live Log
- Keep SPM live log in the main UI.
- Make it wider than the current version.
- Prepare layout so it can later become flexible/resizable.

Safety boundaries:
- No homing.
- No heating.
- No firmware writes.
- No blind lowering below declared floor.
- No XY raster scan during active Phase 2.2.
- Real hardware movement requires explicit confirmation.
- Always read M114 before Z motion.
- Always retract after approach.

Implementation strategy:
- First reorganize UI visually.
- Then connect Z-scanner values.
- Then consolidate Measurement/XY jog information under Phase 2.3.
- Then improve live log width/flex behavior.
- Commit only after tests pass and UI is verified.
