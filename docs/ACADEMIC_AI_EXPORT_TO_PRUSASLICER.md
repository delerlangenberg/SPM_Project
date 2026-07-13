# Academic AI Export to PrusaSlicer

Date: 2026-06-23

## Practical Result

PrusaSlicer normal import is for model files, not raw motion-control G-code.

Use the Academic AI tool to generate `.obj` or `.stl` first. Then import that model into PrusaSlicer, slice with the correct printer/material/profile, and export the final printer G-code from PrusaSlicer.

## Normal Workflow

1. Open `Tools -> Academic AI Print File Export`.
2. Set the printer parameters first: material, nozzle, temperatures, size, thickness/layer Z, speed, line spacing, and export format.
3. Describe the object, surface, lattice, microstructure, or test coupon you want.
4. Choose `obj` or `stl` for normal PrusaSlicer import.
5. Click `Send to AI`.
6. If the printer parameters are unclear, ask AI for parameter advice or click `Use AI Suggested Parameters`, then review the values.
7. Continue the discussion by writing a new message and clicking `Send to AI` again.
8. Repeat discussion until the plan matches the final wish. The studio supports 10+ refinement rounds.
9. Click `Confirm Final`.
10. Click `Create Code`.
11. Click `Save As`.
12. In PrusaSlicer, use `File -> Import -> Import STL/3MF/STEP/OBJ/AMF`.
13. Slice and inspect the generated path.
14. Export print G-code from PrusaSlicer only after inspection.

The generated code/file text is hidden by default. Click `Show Code` only when you want to inspect the OBJ/STL/G-code text.

## Learning Notes

The studio has a local `Learning Notes` field. Use it for simple project memory:

- preferred material and nozzle
- sizes that worked well
- failed ideas to avoid
- printer-specific habits
- preferred export format

These notes are saved locally and included in future AI planning context. This does not train the external AI model; it makes the next request smarter by giving the assistant better project memory.

## G-code Exception

Raw `.gcode` is still available for expert review, but it is not the recommended beginner path.

Use PrusaSlicer `File -> G-code Preview` for an existing `.gcode` file. Do not expect `.gcode` to behave like an imported model.

## Safety Boundary

The operator software does not send Academic AI generated files to hardware.

The AI tool creates a review/export artifact only:

- `gcode_sent = False`
- `execution_allowed = False`
- `review_required = True`

Printer-specific heating, purge, bed preparation, material profile, extrusion calibration, support, and start/end G-code should come from PrusaSlicer or a verified printer workflow.
