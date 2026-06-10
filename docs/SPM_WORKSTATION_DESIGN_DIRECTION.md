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
