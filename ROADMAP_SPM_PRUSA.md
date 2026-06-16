# SPM / Prusa MK4S Project Roadmap

## Current Status

Phase 0 - Safe migration and roadmap setup

Original safety project:
C:\SPM_Project

New active working project:
D:\SPM_Prusa_Project

Rule:
All future development happens in D:\SPM_Prusa_Project.
C:\SPM_Project remains untouched as the fallback copy.

## Main Vision

The project uses the Prusa MK4S hardware as a scanning probe microscope style platform.
The goal is not atomic-level microscopy.
The realistic goal is micrometer-scale scanning, or the best possible resolution within the mechanical and sensor limits of the Prusa MK4S.

The system should be able to scan surfaces, display measured or simulated shapes in software, and later also print or reproduce shapes.

## Three Main Project Parts

Part A - Scanning Probe Microscope mode
Part B - Shape Printing / 3D Printer mode
Part C - AI Scan and Print demonstration mode

## Current Hardware

Platform: Prusa MK4S
Current feedback: nozzle-based feedback
Future feedback: Creality CR-Touch sensor mounted parallel to the nozzle

The CR-Touch will have an offset from the nozzle position.
The software must later support probe_offset_x, probe_offset_y, and probe_offset_z.

## Immediate Bugs Observed During Testing

Bug 1 - Z setpoint does not follow the entered number.
Observed: values like 0, 10, and 2 are entered, but Z stays around 60 mm.
Required: trace Z through GUI input, scan profile, validation, scan runner, MK4S command generation, and display.

Bug 2 - Preview button does not work.
Required: preview must read current GUI parameters, generate the selected surface, show preview, and never move hardware.

Bug 3 - Real MK4S motion does not update the main scan window properly.
Required: real hardware scan loop must update the main scan display live.
If motion is real but values are simulated, label it as: Real MK4S motion with simulated measurement values.

## Phase 0 - Safe Migration

Goal: move active work from C:\SPM_Project to D:\SPM_Prusa_Project.
Completed: project copied to D:\SPM_Prusa_Project.
Completed: important folders and files verified.
Current task: save this roadmap file.
Next task: create or verify Python virtual environment on D drive.

## Phase 1 - Stabilize Existing Scanner

1. Fix Z setpoint handling.
2. Fix preview button.
3. Connect real MK4S scan loop to the live main scan window.
4. Make mode labels clear.
5. Add or update tests.

## Phase 2 - Refactor Half-Ball Into Generated Structure Scan

1. Rename half-ball mode to Generated Structure Scan or AI Scan and Print Demo.
2. Keep half-ball as sphere or half_sphere.
3. Add ShapeProfile.
4. Add generate_surface(scan_profile, shape_profile).
5. Make preview use the new generator.

## Phase 3 - Add Corner-Based Shapes

2 corners -> line or ridge
3 corners -> triangle
4 corners -> square
5 corners -> pentagon
6 corners -> hexagon
7 or more corners -> higher polygon

## Phase 4 - Prepare CR-Touch Sensor Abstraction

1. Add SensorProfile.
2. Keep nozzle feedback as current default.
3. Add CR-Touch as future sensor type.
4. Add probe offset fields.
5. Add calibration placeholder.

## Phase 5 - Object-Based Shapes

First target: CSV height map.
Future targets: STL, OBJ, image-to-heightmap, scanned object to printable object.

## Phase 6 - Academic AI API

AI may suggest scan settings or shape parameters.
Local software must validate all AI output before preview, scan, or print.
AI must never directly move hardware.

## Safety Rules

Preview must never move hardware.
Hardware movement must respect safe X, Y, and Z limits.
Unsafe parameters must be rejected before movement.
The program must not silently replace entered values with unrelated defaults.

## Next Step

Phase 0.4 - Create or verify the Python virtual environment in D:\SPM_Prusa_Project and run tests.

## Phase 0 Completion Checkpoint

Date: 06/16/2026 11:30:50

Phase 0 is complete.

Completed:
- Copied project from C:\SPM_Project to D:\SPM_Prusa_Project.
- Kept C:\SPM_Project as untouched safety fallback.
- Created ROADMAP_SPM_PRUSA.md.
- Created new Python virtual environment on D drive.
- Installed requirements.
- Verified tests from D project: 160 passed.

Next main phase:
Phase 1 - Stabilize Existing Scanner.

Phase 1 tasks:
1. Fix Z setpoint handling.
2. Fix preview button.
3. Connect real MK4S scan loop to the live main scan window.
4. Keep real/simulated measurement labels clear.
5. Keep all safety validation active.
