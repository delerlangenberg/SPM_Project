# SPM Software Professional Phase Roadmap

## Core principle
Each phase is one complete project.  
Each phase solves exactly one problem before the next phase starts.

No full scan behavior is allowed until initialization, XYZ control, Z approach, safety, and GUI control are independently tested.

---

# Phase 6 — Hardware Command Foundation

## Problem
The software must communicate with hardware safely before any scanner movement.

## Scope
- Power ON
- Power OFF
- INFO / STATUS
- SAFE STOP
- Command logging
- Simulated command bus first
- Real command bus later

## Done when
- Commands work in simulation
- Unknown commands fail safely
- Tests pass
- No motion commands exist in this layer

## Current status
Phase 6.1 simulated command bus: PASSED.

---

# Phase 7 — General System Initialization

## Problem
The full SPM system needs one clean initialization sequence.

## Scope
- Detect connected devices
- Load machine profile
- Load limits
- Check serial ports
- Check Prusa/MK4S communication
- Check Z controller communication
- Check sensor/ADC availability
- Build one system status object

## Not allowed
- No scan
- No Z approach
- No XY movement except optional safe identity/status query

## Done when
- One command shows system readiness
- Missing hardware is reported clearly
- Software does not crash if hardware is absent

---

# Phase 8 — XYZ Scanner Control

## Problem
The XYZ scanner must be controlled safely and independently.

## Scope
- X axis test
- Y axis test
- Z axis test as positioning only
- Homing/status query
- Position readback
- Limit checking
- Safe parking

## Not allowed
- No surface approach
- No scan loop
- No feedback control

## Done when
- Each axis can be tested alone
- XYZ status is readable
- Out-of-limit moves are rejected
- Safe parking works

---

# Phase 9 — Z Scanner Approach Development

## Problem
The Z scanner approach must be fully tested before real scanning.

## Scope
- Z-only approach simulation
- Z-only hardware command exchange
- Step-size control
- Retraction
- Contact/signal threshold logic
- Emergency retreat
- Approach logs
- Repeatable test procedure

## Not allowed
- No XY raster scan
- No full scan mode

## Done when
- Z approach behaves exactly as expected
- Safe retreat always works
- Approach can be repeated without crash
- Logs prove each step

---

# Phase 10 — Measurement / Sensor Information Layer

## Problem
The software must read measurement information reliably.

## Scope
- Sensor read command
- ADC/status read
- Simulated signal source
- Real signal source adapter
- Timestamped measurements
- Error handling for disconnected sensor

## Done when
- Sensor values are readable
- Missing sensor fails safely
- Z approach can consume sensor data later

---

# Phase 11 — Main GUI Interface

## Problem
The GUI must become the main safe operator interface.

## Scope
- Main window structure
- System status panel
- Hardware command buttons
- Safety stop button
- Console/log window
- No automatic demo scan
- No crash when button fails

## Done when
- GUI opens reliably
- Buttons call tested backend functions
- Errors are shown in GUI instead of closing the app

---

# Phase 12 — Hardware Control Window

## Problem
Hardware controls need their own clean window/panel.

## Scope
- Power ON/OFF
- INFO
- SAFE STOP
- Device connection status
- Command history

## Done when
- Hardware can be tested from GUI
- Same backend as CLI/tests is used
- No duplicate unsafe logic

---

# Phase 13 — XYZ Control Window

## Problem
XYZ movement needs a separate operator window.

## Scope
- X jog
- Y jog
- Z jog
- Position readback
- Park button
- Limits display
- Disabled buttons when system not initialized

## Done when
- Each axis can be tested from GUI
- Invalid moves are blocked
- Position/status updates correctly

---

# Phase 14 — Z Approach Window

## Problem
Z approach needs a dedicated controlled workflow.

## Scope
- Step size
- Threshold
- Start approach
- Stop approach
- Retract
- Live approach log
- Approach result summary

## Done when
- Z approach works from GUI exactly like tested backend
- Emergency retreat works
- No XY scan starts from this window

---

# Phase 15 — Scan Preparation Window

## Problem
Scan setup must be separated from scan execution.

## Scope
- Scan area
- Resolution
- Speed/feedrate
- Mode selection
- Safety validation
- Dry-run preview

## Done when
- Invalid scan profiles are rejected
- Dry-run path is visible/logged
- No hardware scan starts accidentally

---

# Phase 16 — Real Scan Execution

## Problem
Only after all previous phases, real scanning can be enabled.

## Scope
- Controlled raster scan
- Measurement capture
- Live progress
- Abort
- Save data
- Save image/output

## Done when
- Scan completes without crash
- Abort is safe
- Data is saved
- System returns to safe state

---

# Phase 17 — Stability, Packaging, and Handoff

## Problem
The software must become reliable for repeated lab use.

## Scope
- Full test suite
- Operator guide
- Troubleshooting guide
- Version backup
- Git commit
- Release note

## Done when
- Clean git status
- All tests pass
- Documentation is complete
- Versioned backup exists

---

# Working rule for every phase

Each phase must include:

1. Backend module
2. Unit tests
3. CLI or minimal test entry point
4. GUI only after backend passes
5. Documentation update
6. Full tests
7. Backup and git commit only at complete milestone

---

# Codex / New Chat Continuation Rules

When this project is continued in Codex or a new AI coding session, the assistant must follow this roadmap strictly.

## Mandatory workflow

1. Read this file first:
   - docs\SPM_PROFESSIONAL_PHASE_ROADMAP.md

2. Work on only one phase at a time.

3. Work on only one problem inside that phase until it is solved.

4. Do not jump ahead to scan execution, GUI expansion, or real hardware movement before the required lower phase is complete.

5. For every implementation step, provide:
   - exact code or command to run
   - exact test command to run
   - expected output
   - next decision based on observed output

6. Every phase must be treated as a complete mini-project:
   - backend module
   - tests
   - CLI/minimal test entry point
   - GUI only after backend passes
   - documentation update
   - full test suite
   - version backup
   - git commit only at completed phase milestone

7. Never silently remove safety checks.

8. Never introduce automatic demo scan behavior.

9. Never allow scan motion before:
   - initialization phase is complete
   - XYZ phase is complete
   - Z approach phase is complete
   - sensor information phase is complete
   - GUI safety controls are complete

10. At the end of every completed phase, write:
    - what was achieved
    - what files changed
    - test result
    - backup/version location
    - git commit hash
    - next phase start point

## Current verified status

- Professional roadmap file exists.
- Safe simulated hardware command bus exists.
- Hardware command bus tests passed.
- Full test suite passed: 114 passed.
- Current next work should remain inside Phase 6 until Phase 6 is fully complete.

---

# Phase 6 Progress Log — Hardware Command Foundation

## Completed so far

## 6.1 Simulated hardware command bus
File:
- core\hardware\hardware_command_bus.py

Implemented safe commands:
- POWER_ON
- POWER_OFF
- INFO
- SAFE_STOP

Safety behavior:
- No motion commands.
- Unknown commands fail safely.
- MOVE_X is rejected.
- The command bus only simulates hardware state.

Test:
- tests\test_hardware_command_bus.py

Result:
- 3 passed

## 6.2 CLI command entry point
File:
- core\application\hardware_command_cli.py

Implemented:
- python -m core.application.hardware_command_cli INFO
- python -m core.application.hardware_command_cli POWER_ON
- python -m core.application.hardware_command_cli POWER_OFF
- python -m core.application.hardware_command_cli SAFE_STOP

Safety behavior:
- CLI only accepts safe commands.
- Motion commands are rejected by argparse.

Test:
- tests\test_hardware_command_cli.py

Result:
- 6 passed together with command bus tests

## Verified manual command output

INFO:
- success=True
- response=OK: SPM HARDWARE SIMULATED; POWER=OFF

POWER_ON:
- success=True
- response=OK: POWER ON

SAFE_STOP:
- success=True
- response=OK: SAFE STOP; POWER OFF

## Current phase decision
Continue inside Phase 6.
Do not start Phase 7 yet.

Next Phase 6 target:
- add persistent command log file or GUI-safe service wrapper
- then run full test suite
- then create phase backup and git commit only when Phase 6 is complete

---

# Phase 6 Completion Candidate

## Completed
- Safe simulated hardware command bus
- Safe CLI command entry point
- Persistent command log
- Motion commands rejected
- Scan commands not present
- Manual CLI test successful
- Log file created at logs\hardware_command_log.csv

## Verified manual output
- INFO returned success=True
- POWER_ON returned success=True
- SAFE_STOP returned success=True
- Log rows are written correctly

## Phase 6 safety status
- No XYZ movement
- No Z approach
- No scan execution
- No automatic demo scan

---

# Phase 7 Progress Log — General System Initialization

## Completed
- Confirmed Prusa MK4 controller on COM5
- Stored hardware profile in config\spm_hardware_initialized_profile.json
- Added safe profile loader
- Added read-only startup initializer
- Added startup CLI
- Verified real hardware startup

## Read-only startup commands
- M115
- M105
- M119

## Verified hardware
- Port: COM5
- Baudrate: 115200
- Firmware: Prusa-Firmware-Buddy 6.2.4+8909
- Machine: Prusa-MK4
- UUID: cede2a2f-41a2-4748-9b12-c55c62f367ff

## Safety status
- No movement
- No homing
- No scan
- No Z approach

## Tests
- Full suite passed: 125 passed
