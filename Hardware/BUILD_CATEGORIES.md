# SPM Scanner Build Categories

The scanner build should be planned in modules.

## A. Mechanical frame

Includes:

- base plate
- scanner body
- mounting brackets
- sample holder
- probe holder
- vibration isolation

Main requirement:

The mechanical frame must be rigid and stable before fine Z-control or signal measurement becomes useful.

---

## B. XY positioning

Includes:

- XY stage or scanner
- motors / piezo / linear actuators
- guides
- travel limits
- controller interface

Main requirement:

XY movement must be repeatable and must stay inside configured software and hardware limits.

---

## C. Z control and approach

Includes:

- Z actuator
- Z driver electronics
- limit switch or safe stop
- approach/retract logic
- emergency stop path

Main requirement:

Z movement must be safe. Software dry-run must be completed before real Arduino movement is enabled.

---

## D. Signal acquisition

Includes:

- sensor or probe signal
- amplifier
- DAQ
- filtering
- grounding
- shielding

Main requirement:

The signal chain must be tested independently before it is connected to raster scanning.

---

## E. Workstation software

Includes:

- PySide6 GUI
- scan validation
- dry-run scan
- hardware scan
- plot generation
- future live image/raster view
- future signal monitor
- future logs/safety panel

Main requirement:

The software must remain safe-first, test-covered, and modular.
