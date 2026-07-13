# Phase 2.1H.2 / 2.3A MK4S Motion Limits and Scan-Speed Model

Purpose:
Define the engineering limits used by the SPM Prusa MK4S educational scanner.

Machine:
Original Prusa MK4S.

Physical build envelope:
- X: 250 mm
- Y: 210 mm
- Z: 220 mm

Firmware motion parameters:
- X steps/mm: 100
- Y steps/mm: 100
- Z steps/mm: 400

Command resolution:
- X/Y: 0.01 mm = 10 micrometers
- Z: 0.0025 mm = 2.5 micrometers

Hardware normal feedrate limits:
- X: 300 mm/s
- Y: 300 mm/s
- Z: 40 mm/s

Educational SPM software recommendations:
- Do not use full printer speed for scanning.
- Recommended demo scan speed: 1 to 10 mm/s.
- Default demo scan speed: 5 mm/s.
- Recommended travel speed: 20 mm/s.
- Recommended Z approach speed: 0.05 to 0.50 mm/s.
- Default Z approach speed: 0.10 mm/s.
- Recommended fine Z step: 10 micrometers.
- Recommended retract height: 25 mm above declared surface.

Important safety distinction:
The listed X/Y/Z command resolution is motion command resolution.
It is not AFM/STM measurement resolution.
Real surface resolution depends on a verified sensor or feedback channel.

Software files:
- core/web/mk4s_motion_limits.py
- web/operator_console/mk4s_motion_limits.json
- tests/test_mk4s_motion_limits.py
