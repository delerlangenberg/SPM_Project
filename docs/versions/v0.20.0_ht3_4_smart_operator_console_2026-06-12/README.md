# v0.20.0 - HT3.4 Smart Operator Console

Date: 2026-06-12

## Purpose

Make the hardware-test interface feel like smart scientific software instead of a manual button board.

The operator feedback was clear: there were too many visible buttons, and the workflow was too slow. This phase adds a smart first screen with self-assessment, readiness scoring, and a recommended next action.

## Main Changes

- Version updated to `v0.20.0`.
- Phase label updated to `HT3.4 Smart Operator Console`.
- Added a top-level `Smart Operator Console`.
- Added `Smart System Check`.
- Added readiness state and score.
- Added plain-language recommendation.
- Added self-assessment details.
- Expert hardware controls are hidden by default.
- Added `Show expert hardware controls`.
- Added `Prepare Motion Test`, which opens expert controls and selects a conservative first motion setup.

## Local Self-Assessment

The new local assessment checks:

- controller identity from `M115`
- temperature/status response from `M105`
- endstop status from `M119`
- XYZ position from `M114`
- parsed XYZ position against confirmed MK4S software limits

Readiness states:

- `READY_FOR_SUPERVISED_MOTION`
- `CHECK_BEFORE_MOTION`
- `NOT_READY`

## Academic AI Boundary

The Academic AI API can be integrated later for:

- log summaries
- experiment notes
- scan interpretation
- report generation
- operator training explanations

It must not:

- send G-code
- start motion
- override safety limits
- decide that unsafe hardware is safe

## Launch Command

```powershell
.\.venv\Scripts\python.exe -m core.application.hardware_test_console_gui
```

## Verification

```powershell
.\.venv\Scripts\python.exe -m py_compile core\application\hardware_test_console_gui.py core\system\smart_hardware_assessment.py
.\.venv\Scripts\python.exe -m pytest tests\test_hardware_test_console_gui.py tests\test_smart_hardware_assessment.py tests\test_hardware_test_controls.py tests\test_hardware_information_exchange.py -q
.\.venv\Scripts\python.exe -m pytest -q
```

Results:

- Focused GUI/control/information/smart-assessment tests: 21 passed.
- Full project suite: 152 passed.

## Files Changed

- `core/application/hardware_test_console_gui.py`
- `core/system/smart_hardware_assessment.py`
- `tests/test_hardware_test_console_gui.py`
- `tests/test_smart_hardware_assessment.py`
- `docs/TWO_LAYER_SPM_DEVELOPMENT_ROADMAP_2026-06-12.md`

## Next Phase

HT3.5 should add a guided one-step motion wizard with operator confirmation after each physical axis response:

1. smart check
2. read XYZ
3. safe retract if needed
4. one 1 mm axis step
5. operator confirms observed direction
6. software records the observation
7. repeat for X, Y, and Z
