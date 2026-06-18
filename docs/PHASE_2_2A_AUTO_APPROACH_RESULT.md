# Phase 2.2A Result - Controlled Z Auto-Approach Test

Completed: 2026-06-18 17:26:02

Test setup:
- Target object: 1 euro coin placed on foam.
- Foam/object region expected near Z=55 mm.
- Target XY center: X125 Y105.
- Approach script: tools/phase_2_2a_auto_approach_coin.py.
- Movement type: controlled real hardware Z approach.
- Hard floor: Z=55 mm.
- Retract: Z=80 mm.

Observed result:
- Printer moved to center.
- Z approached downward in guarded steps.
- M119 was checked during approach.
- M119 continued to report:
  - x_min: open
  - x_max: open
  - y_min: open
  - y_max: open
  - z_min: open
  - z_max: open
- Script retracted successfully to Z=80 mm.
- Final result: NO_M119_CONTACT_TRIGGER_BEFORE_FLOOR.

Conclusion:
- The motion pathway is safe.
- M119 is not a valid confirmed contact detector for this setup.
- We must not claim true automatic contact detection from M119.
- Future STM/auto-approach requires a real measurable contact channel:
  1. external contact sensor,
  2. loadcell/probe signal exposed through a usable command/API,
  3. electrical STM current threshold,
  4. or another verified sensor path.

Safety rule for next phases:
- No blind lowering below the configured floor.
- No automatic contact mode unless the contact signal is verified.
- Current Z approach remains a guarded distance approach, not a real contact-detection approach.
