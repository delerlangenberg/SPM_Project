# SPM Phase 6 Roadmap — Hardware Power + Information Exchange Layer

## Goal
Build the software in two safe layers before any real scan behavior:

1. **Hardware Test Layer**
   - Buttons/commands for:
     - Power ON
     - Power OFF
     - Request status/info
     - Send basic command and receive response
   - No scan movement.
   - No automatic demo scan.
   - No unsafe Z or XY movement.

2. **Real Control Layer**
   - Only after the hardware test layer is stable.
   - Reuse the tested communication functions.
   - Add controlled scan features phase by phase.

## Immediate problem observed
Demo scan was clicked, started, then the software closed automatically.
Before debugging full scan logic, we reduce scope to hardware communication only.

## Phase 6.1
Create/verify a safe hardware communication test entry point.

## Phase 6.2
Add GUI buttons for:
- Hardware Power ON
- Hardware Power OFF
- Hardware Info / Status
- Emergency / Safe Stop if available

## Phase 6.3
Connect buttons to backend safely.
All commands must log:
- command sent
- response received
- success/failure
- timestamp

## Phase 6.4
Only after tests pass, connect this to the real GUI layer.

## Safety rule
No scan, no automatic movement, no Z approach, no demo scan until hardware command exchange is fully tested.
