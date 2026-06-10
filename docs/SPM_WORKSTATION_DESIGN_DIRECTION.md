# SPM Workstation Design Direction

## Target software style

The project should evolve toward a simplified professional SPM workstation similar in concept to:

- Bruker NanoScope-style AFM/SPM control software
- Scienta Omicron MATRIX-style modular SPM control software

This does not mean copying those systems. It means adopting the same type of workflow:

1. System connection
2. Scan setup
3. Z-control / approach
4. Live image or height-map display
5. Signal monitoring
6. Data saving and analysis
7. Safety and status logging

## Current safe baseline

The current working baseline is:

- Phase 4.5 GUI scan launcher
- Safe motion limits
- Dry-run scan
- Hardware scan
- CSV output
- Automatic PNG plot generation
- Color map selection
- Phase 5.1 Z dry-run driver
- Z dry-run GUI controls
- Z dry-run limit validation

This baseline must not be replaced by the old GitHub GUI.

## Old GitHub version

The old GitHub version contains useful ideas:

- QMainWindow layout
- dock widgets
- serial port selector
- Z regulation panel idea
- live plot / visualization structure
- hardware and simulation folders

But it should not be merged directly because it would remove or overwrite working safe files.

## New design path

The project should move gradually from the current safe QWidget GUI toward a modular workstation:

Phase A — current QWidget safe GUI
- keep working

Phase B — add safe Z-control panel behavior
- dry-run only first
- validated limits
- no uncontrolled hardware movement

Phase C — add live plot preview panel
- still based on saved CSV/PNG first
- later live updates during scan

Phase D — migrate to QMainWindow / dock-style workstation
- System Control dock
- Scan Setup dock
- Z Control dock
- Live Plot dock
- Log dock

Phase E — real probe signal integration
- Arduino/Z control
- ADC/sensor input
- approach/retract sequence
- signal acquisition during raster

## Design rule

Safety first:
- dry-run before hardware
- motion limits before movement
- no direct merge from old GitHub
- backup before each phase
- Git commit after stable phase/milestone only

---

## Updated Phase Roadmap after Phase 5.7

### Phase 5.7 â€” Scan-start confirmation and scan safety messaging

Purpose:
- Add operator confirmation before scan execution.
- Show scan mode, XY scan area, Z height, resolution, output file, color map, and safety state.
- Keep dry-run safe by default.
- Repair GUI field naming so scan confirmation uses the existing output-file widget.

Status:
- In progress.
- Automated confirmation flow added.
- Crash repaired by using `self.output_file` instead of nonexistent `self.output_path`.

---

### Phase 5.8 â€” Hardware execution separation and safety clarification

Purpose:
- Separate dry-run scan execution from hardware execution more clearly.
- Hardware execution must have its own professional confirmation.
- Hardware execution must display real-risk state clearly.
- Do not silently mix dry-run Z scanner controls with Prusa/XY hardware scan execution.
- Hardware mode must be visually distinct from dry-run mode.

Safety rule:
- Real hardware movement must remain explicit.
- Hardware execution needs clear operator confirmation.
- Hardware status must show connection state, port, mode, and last known machine state.

---

### Phase 6 â€” Professional SPM workstation interface redesign

Purpose:
Move from a simple test GUI to a workstation-style SPM interface.

The interface must be organized around the physical meaning of the scanner:

1. XY Scan Setup
   - X min / X max
   - Y min / Y max
   - XY resolution
   - XY feedrate
   - scan output file
   - color map
   - scan mode

2. Z Scanner / Height Control
   - Z height
   - approach
   - retract
   - Z step size
   - Z safe limits
   - Z dry-run driver state
   - height-related safety messages

3. Hardware / System Connection
   - machine connection status
   - port
   - baudrate
   - connect / disconnect
   - last hardware state
   - real hardware execution state
   - hardware readiness

4. Safety and Status Layer
   - global scan limits
   - critical action confirmations
   - safe-position status
   - warning and cancellation logs
   - clear operator mode labels

5. Live Data / Plot Area
   - last generated raster image
   - scan output preview
   - selected color map
   - future live signal display

6. Operator Log
   - scan events
   - Z scanner events
   - hardware events
   - safety confirmations
   - failures and cancellations

---

### Phase 6.1 â€” Separate XY scan setup, Z scanner control, hardware status, and safety/status layer

Purpose:
- Rebuild the GUI structure into clear workstation panels.
- Keep existing functionality.
- Do not enable new unsafe hardware movement.
- Make buttons stateful and visually meaningful.

Button color direction:
- Green: ready / safe to start / ready to connect
- Red: connected / active hardware state / critical action available
- Grey: unavailable / disabled
- Yellow or orange later: warning / caution state

Important correction:
- In SPM terminology, approach and retract belong to the Z scanner / height-control workflow.
- XY scan area belongs to raster scan setup.
- Hardware connection belongs to a separate system/hardware panel.
- Safety limits apply globally to all scanner actions.
