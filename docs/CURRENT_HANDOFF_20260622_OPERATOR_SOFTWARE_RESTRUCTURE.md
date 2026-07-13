# SPM Prusa Project Handoff - Operator Software Restructure

Date: 2026-06-22
Current desktop software version: v0.2.23
Primary app: `D:\SPM_Prusa_Project\core\application\operator_workstation_software.py`

## Executive Summary

The project is migrating from the web operator console to a desktop-style PyQt5 operator workstation. The web UI has been preserved as a backup/snapshot, but current development focus is the desktop application because hardware reaction, live feedback, safety shutdown, and operator workflow need to feel like professional instrument software rather than a hobby webpage.

The current direction is:

1. Main window opens with only Phase 2.1 System Control.
2. Tools menu opens independent instrument windows:
   - Phase 2.2 Z Scanner
   - Phase 2.3 Measurement Control
   - Phase 2.4 Live Log
3. Measurement Control owns XY raster parameters and signal/topography views.
4. Z Scanner owns all Z-related controls, including target Z, auto approach, live Z trace, tapping limits, retract, and emergency stop.
5. Real tapping scan should follow the microscopy logic:
   - move to XY point
   - approach/tap in Z
   - detect contact
   - record exact contact Z as table-referenced surface height
   - retract fully to a safe Z
   - move to the next XY point
   - update line and topography windows continuously

Important physical correction made on 2026-06-22:

- The scanner plate / XY table is `Z=0`.
- The current test sample is aluminum foil on 8 mm foam, so expected contact is around positive Z above the plate, not around the old high-Z parking values.
- The tapping setpoint is contact detection. The system descends until the nozzle/load-cell path detects surface contact, records that Z as the surface height, then retracts.
- There is no optical AFM laser feedback yet. During this stage the printer nozzle/load-cell/contact channel is the temporary feedback path.

## Current Code State

### Desktop App

File:

`D:\SPM_Prusa_Project\core\application\operator_workstation_software.py`

Current app version:

`APP_VERSION = "v0.2.23"`

Important classes:

- `OperatorWorkstation`
  - Main PyQt window.
  - Now intended to show only Phase 2.1 System Control on startup.
  - Owns hardware worker state, safe shutdown, logs, signal windows, scan state, and tool windows.

- `ZScannerWindow`
  - Independent tool window for Phase 2.2 Z Scanner.
  - Uses `owner.build_z_panel()`.
  - Closing the window hides it instead of destroying state.

- `MeasurementWindow`
  - Independent tool window for Phase 2.3 Measurement Control.
  - Owns XY range, point count, line count, scan direction, speed, simulation surface, embedded line view, and embedded topography view.
  - It no longer duplicates Z scanner controls.
  - It consumes Z settings from the independent Z Scanner window.

- `LiveLogWindow`
  - Independent Phase 2.4 live log window.
  - Clear/download controls are included.

- `AcademicGCodeWindow`
  - Independent tool window for review-only AI-style print model/file generation.
  - Open from `Tools -> Academic AI Print File Export`.
  - UI title: `Academic AI Print File Studio`.
  - Prompt-first AI helper workflow: the user describes what they want to build, AI proposes/refines a build plan, the user discusses improvements until the plan is right, the user agrees to the final plan, then final file generation is enabled.
  - Includes editable print parameters: overall size, thickness/layer Z, material, nozzle diameter, nozzle/bed temperature, print speed/feedrate, line spacing, and export format.
  - Generated code/file text is hidden by default and shown only through `Show Code`.
  - Local `Learning Notes` are saved in `config/academic_ai_print_learning_notes.txt` and included in future AI planning context. This is project memory, not external model training.
  - Default export is OBJ/STL because PrusaSlicer normal import supports model files such as STL/3MF/STEP/OBJ/AMF.
  - G-code remains available only as an expert review file through PrusaSlicer G-code Preview.
  - Academic AI may advise pattern design, but generated files are not sent to hardware.
  - Output must be reviewed before printing and should use printer-specific slicing, start/end G-code, heating, purge, and material profiles from a normal PrusaSlicer workflow.

- `CRTouchPrepWindow`
  - Independent preparation/readiness window for CR Touch probe integration.
  - Open from `Tools -> CR Touch Probe Prep`.
  - Based on `CRTouch_SPM_FINAL_Project.docx`.
  - Real CR Touch control remains disabled until wiring, trigger, magnet, and repeatability tests are confirmed.

- `SignalPlotWidget`
  - Draws line mode and topography mode.
  - Recent fix: now draws point markers and visible flat topography cells, so one-point or flat-Z data is no longer invisible.

- `ZTraceWidget`
  - Live Z trace with full/auto/zoom display.

### Real Scan Backend

File:

`D:\SPM_Prusa_Project\core\web\real_scan_control.py`

Important functions/classes:

- `run_real_constant_z_scan`
  - Moves XY at one selected Z.
  - Reads `M114` at each point.
  - This is not tapping. It is useful for position/raster testing.

- `run_real_foil_tap_scan`
  - Experimental tapping scan.
  - Intended workflow: XY move, Z approach, contact detection, record contact Z, retract, next point.
  - Uses experimental `M119 z_min` contact detection until a real sensor/backend is installed.
  - Uses table-referenced height: `surface_height = contact_z - table_z_mm`, with `table_z_mm = 0.0` by default.
  - Current pre-scan sequence: retract to full safe Z, move to XY minimum, then begin approach/measurement.
  - Current safety behavior: full retract after every tap attempt, including no-contact abort.

- `FoilTapConfig`
  - Table reference Z, Z setpoint/contact limit, tapping range above setpoint, approach speed, step sizes, local retract distance, full retract Z, contact source, abort behavior.

Safety gates:

Real scan is locked unless:

`SPM_WEB_ALLOW_REAL_SCAN=1`

Foil/tapping scan is additionally locked unless:

`SPM_WEB_ALLOW_FOIL_TAP=1`

## Current User Workflow

### Launch

From PowerShell:

```powershell
cd D:\SPM_Prusa_Project
.\spm.bat
```

`spm.bat` enables the read-only hardware, health-motion, real-scan, and foil-tap gates before opening the desktop operator software.

### Phase 2.1 System Control

This is the only card shown in the main window.

It includes:

- port selection
- connect read-only
- disconnect
- diagnosis
- AI error correction
- safe standby to `X125 Y105 Z120`

The user confirmed Safe Standby works.

Important safety behavior:

When the user closes the desktop software, it should:

1. request active scan stop
2. park at safe standby `X125 Y105 Z120`
3. disconnect
4. only then close

This has been implemented and previously tested with logs.

### Phase 2.2 Z Scanner

Open from:

`Tools -> Z Scanner`

It should contain all Z-related behavior:

- current Z readout
- count/clearance readouts
- live Z signal window
- full/auto/zoom Z trace scale
- Z setpoint / contact limit
- tapping range above setpoint
- expected surface Z guide
- approach speed
- table reference Z = `0.000`
- full retract Z
- read Z
- manual approach to setpoint
- auto approach with feedback/simulation
- retract Z
- STOP Z

Z target/setpoint belongs here, not in Measurement Control. Keep this window simple: setpoint, tapping range, approach speed, retract, stop.

### Phase 2.3 Measurement Control

Open from:

`Tools -> Measurement Control`

It should contain XY/raster behavior only:

- X range mm
- Y range mm
- X points
- Y lines
- scan direction: `X+`, `X-`, `Y+`, `Y-`
- scan speed
- simulation surface
- calculated primary step and line step
- MK4S command resolution note
- Start Constant-Z Raster
- Start Tapping Scan 50x50
- Start Simulation
- Pause
- Stop
- Open Line Window
- Open Topography Window
- embedded line mode preview
- embedded topography preview

Important distinction:

- `Start Constant-Z Raster` only moves XY at the target Z and reads M114.
- `Start Tapping Scan 50x50` is the intended foil/foam feature measurement mode.
- Direction controls define the primary scan vector:
  - `X+`: scan increasing X, step Y
  - `X-`: scan decreasing X, step Y
  - `Y+`: scan increasing Y, step X
  - `Y-`: scan decreasing Y, step X

### Phase 2.4 Live Log

Open from:

`Tools -> Live Log`

The log should be useful for operator, service, and development:

- timestamped line-by-line events
- clear log
- download log
- hardware command summaries
- scan point summaries
- safety shutdown events

## Hardware Context

Hardware is a Prusa MK4S-based scanner used as an SPM/AFM-like mechanical platform.

The nozzle/load-cell behavior is being used as a Z sensing concept. The user placed foam and aluminum foil in the center of the XY scanner to test tapping/height readback.

Important known coordinates/settings from current project:

- safe standby target: `X125 Y105 Z120`
- typical center: `X125 Y105`
- recent requested tapping test: 50 x 50 mm from center
- requested raster: 10 points in each direction
- foam/foil test target: contact/topography measurement by tapping each XY point
- Z physical reference: scanner plate / XY table is `Z=0`
- test surface: aluminum foil on approximately 8 mm foam, centered on the XY scanner

## Academic AI Integration

Files:

- `D:\SPM_Prusa_Project\core\ai\academic_ai_client.py`
- `D:\SPM_Prusa_Project\docs\API_SPM.txt`
- `D:\SPM_Prusa_Project\docs\User manual Academic AI 3.0 - V1.0_en_AI-translated.pdf`

Academic AI 3.0 is integrated through a client. Credentials are intentionally not copied into this handoff. They are stored in `docs/API_SPM.txt` and/or environment variables.

Current default model was previously updated to a newer useful model for the project.

AI Error Correction exists in System Control and is intended to help diagnose operator/hardware state from logs and payloads.

Academic AI G-code export was added in v0.2.11, upgraded in v0.2.12, converted to a true AI helper in v0.2.13, and corrected in v0.2.14 to prefer PrusaSlicer-importable model files:

- File: `D:\SPM_Prusa_Project\core\ai\academic_gcode_generator.py`
- Workflow document: `D:\SPM_Prusa_Project\docs\ACADEMIC_AI_EXPORT_TO_PRUSASLICER.md`
- Tool window: `Tools -> Academic AI Print File Export`
- Current concept resolver:
  - prompts mentioning gold or atomic islands resolve to a `gold_3x3` concept
  - prompts mentioning hex/honeycomb resolve to a hexagonal concept
  - prompts mentioning bravais/lattice/crystal resolve to a Bravais-style lattice
  - prompts mentioning lines/grating/stripes resolve to parallel micro-lines
- Operator inputs:
  - `What do you want to build?`: natural language description, with a gray placeholder example that can be overwritten
  - `Overall size mm`: XY size of the generated concept
  - `Thickness / layer Z mm`: print layer height for the concept path
  - `Print feedrate mm/min`: motion speed used when expert G-code is generated
  - `Line spacing mm`: spacing for line/grating concepts
  - `Export format`: `obj`, `stl`, or expert-only `gcode`
- Safety contract:
  - `gcode_sent = False`
  - `execution_allowed = False`
  - `review_required = True`
- The generated OBJ/STL/G-code file is a review/export artifact only. The operator software does not send it to the printer.
- v0.2.18 workflow:
  - First set printer parameters manually, or ask AI for parameter advice and apply the suggestion locally.
  - `Send to AI`: sends the current user request, printer parameters, learning notes, and chat history.
  - User can repeat `Send to AI` for 10+ refinement rounds until the plan is right.
  - `Confirm Final`: accepts the current plan and enables final generation.
  - `Create Code`: creates the internal OBJ/STL/G-code artifact, still not saved and not sent.
  - `Save As`: lets the user choose where to save the file.
  - `Show Code`: reveals the generated file text only when the user wants to inspect it.
- The text panel is not a visual preview. It is a decision/plan panel. Real path preview must happen in PrusaSlicer or a G-code viewer.
- Normal PrusaSlicer workflow:
  - Save `.obj` or `.stl`.
  - In PrusaSlicer use `File -> Import -> Import STL/3MF/STEP/OBJ/AMF`.
  - Slice/export print G-code from PrusaSlicer.
  - Use `.gcode` only through `File -> G-code Preview` or another G-code viewer.
  - Inspect XY path, Z height/thickness, extrusion, speed, travel moves, and printer-specific start/end behavior.
  - Only after visual review should it move into a print workflow.

CR Touch preparation was expanded in v0.2.11:

- Source document: `C:\Users\SPM\Downloads\CRTouch_SPM_FINAL_Project.docx`
- Project interpretation:
  - CR Touch becomes a contact-based Z probe for macro-scale SPM.
  - Recommended tip: rigid steel needle, about 1 mm diameter, cut to about 18 mm.
  - Optional safer tip: P50/P75 pogo pin, but it requires a glued 2x2 mm magnet and is less precise because of the double-spring system.
  - Guide: PTFE tube, 2 mm OD / 1 mm ID, 10-15 mm guide length.
  - Mechanical requirement: probe axis must be vertical and move smoothly with minimal friction.
  - Manual test: power sensor, press probe manually, verify stable trigger point, adjust magnet if unstable.
- Current state:
  - CR Touch real hardware path remains disabled.
  - The software exposes readiness/safety/test checklist and a read-only M119 status action.
  - CR Touch should not be wired into the automatic Z approach path until repeatable manual trigger/open transitions are verified.

## Current Test Status

Focused tests after the v0.2.14 Academic AI export correction:

```powershell
cd D:\SPM_Prusa_Project
.\.venv\Scripts\python.exe -m pytest tests\test_academic_gcode_generator.py tests\test_operator_workstation_software.py -q
```

Expected result:

Academic AI export and operator-workstation tests pass.

Previous full suite status before this v0.2.14 correction was:

`257 passed`

Full suite should be rerun after this handoff:

```powershell
cd D:\SPM_Prusa_Project
.\.venv\Scripts\python.exe -m pytest -q
```

## Current Git/Workspace Notes

The working tree is dirty and includes many existing changes across config, backend, web console, desktop app, docs, and tests. Do not reset or revert unrelated files.

The desktop app and several support files currently appear as untracked/new in git status. This is expected from the migration work.

Use the Git bundled with GitHub Desktop if normal `git` is not available in PowerShell:

```powershell
& 'C:\Users\SPM\AppData\Local\GitHubDesktop\app-3.5.12\resources\app\git\cmd\git.exe' status --short
```

## Known Problems / Open Engineering Work

### 1. Tapping Contact Source Is Still Experimental

Current foil/tap mode uses `M119 z_min` as a contact source. This may not be the final signal path.

Needed:

- confirm real Prusa/load-cell contact signal exposed by firmware/API
- replace or augment `M119 z_min` if needed
- record contact confidence/source in every measurement point

### 2. Pause Needs Hardware-Level Confidence

Pause was wired to the real scan pause event, but real hardware command boundaries still matter. It pauses between points/commands, not necessarily instantly during a long G-code motion.

Needed:

- keep stop as highest priority
- consider shorter motion chunks during tapping descent
- consider emergency `M410` or firmware-supported quick stop if safe and supported

### 3. Z Scanner Must Be the Single Source of Truth

Current restructure moved the UI in the right direction. Verify all measurement scan paths use:

- `owner.target_z`
- `owner.feedback_gain`
- `owner.tap_start_z`
- `owner.tap_min_z`
- `owner.tap_retract_z`
- `owner.full_retract_z`

Do not add Z parameters back into Measurement Control.

### 4. Main Window Should Stay Clean

Main window should remain System Control only. Tool windows are opened from the menu.

Future tools can be added under `Tools`.

### 5. Signal Windows Need Real Hardware Validation

The drawing logic now handles flat and one-point data. Need hardware validation that:

- line preview updates after every measured point
- topo preview accumulates each line
- external line/topography windows update too
- contact Z is used as plotted value in tapping mode

### 6. Measurement Modes Need Final Naming

Current names:

- Start Constant-Z Raster
- Start Tapping Scan 50x50
- Start Simulation

Recommended final model:

- Simulation Scan
- Constant-Z Hardware Raster
- Tapping Height Scan

### 8. AFM/SPM Tapping Principle For This Project

The correct mental model is not optical AFM feedback. The project currently uses a printer-nozzle/load-cell/contact signal as a temporary surface detector.

For each point:

1. Retract to safe travel height.
2. At scan start, move to the XY minimum reference/start coordinate.
3. Move XY to the next raster point.
4. Descend from `Z setpoint + tapping range` toward the Z setpoint/contact limit.
5. Stop when the nozzle/contact channel indicates touch.
6. Store the contact Z as surface height above the table.
7. Retract fully before moving laterally.

For the current foam/foil sample, if the table is Z=0 and the foam/foil is about 8 mm high, contact should be near Z=8 mm.

Button color rule added in v0.2.9:

- Start/connect/approach buttons are green.
- Stop/disconnect buttons are red.
- Retract is styled red because it is a safety action.

v0.2.10 correction from log `spm_operator_software_20260622_183601.txt`:

- The failed tapping scan searched from `Z=32` down to `Z=12`.
- The test foil/foam surface was expected near `Z=8`.
- Therefore the scan stopped above the physical surface and correctly reported no contact.
- The software now blocks this impossible configuration when `Z setpoint/search lower limit >= expected surface Z`.
- No-contact errors now explicitly tell the operator to lower the Z search limit below expected surface height or verify the contact feedback channel.
- Tapping scan now full-retracts after each tap attempt instead of retracting only to the tap-start height.

### 7. Professional UI Polish Still Needed

The architecture is now cleaner, but UI polish can continue:

- consistent spacing/sizing between tool windows
- status bar with connection/mode/worker state
- disabled buttons while busy
- clearly colored stop/emergency controls
- persistent last-used settings
- instrument-style tabular parameter review before scan start

## Recommended Next Session Plan

1. Run full tests:

```powershell
cd D:\SPM_Prusa_Project
.\.venv\Scripts\python.exe -m pytest -q
```

2. Launch app with real scan gates:

```powershell
cd D:\SPM_Prusa_Project
.\spm.bat
```

3. In the app:

- Main window: connect with System Control.
- Tools -> Z Scanner:
  - read Z
  - set Z setpoint/contact limit using table Z=0 as the reference
  - set tapping range above the setpoint
  - set approach speed
  - for the 8 mm foam/foil test, tapping start must be above expected foil height and the setpoint/contact limit can be 0
  - full retract Z should be high enough for safe lateral travel
  - confirm STOP Z works
- Tools -> Measurement Control:
  - set XY range 50 x 50
  - set 10 x 10 points
  - select X+, X-, Y+, or Y- direction
  - confirm primary step and line step are sensible for the motor resolution
  - start with simulation and verify plots
  - then run tapping scan only when the scanner is physically safe

4. Watch:

- hardware movement
- live Z trace
- line preview
- topography preview
- live log

5. If tapping moves XY only:

- confirm the user clicked `Start Tapping Scan 50x50`, not `Start Constant-Z Raster`
- inspect the live log for `TAPPING SCAN`
- inspect `run_real_foil_tap_scan`
- confirm `SPM_WEB_ALLOW_FOIL_TAP=1`

## Definition Of Done For Phase 2

Phase 2.1 System Control is done when:

- connect/disconnect reliably work
- diagnosis visibly tests safe motion
- AI correction gives useful operator/service advice
- safe standby works
- close always parks and disconnects safely

Phase 2.2 Z Scanner is done when:

- target Z applies reliably
- auto approach works or simulates clearly until sensor backend is ready
- retract works
- STOP Z reacts quickly enough for safety
- live Z trace updates per Z movement/contact step
- all Z/tap parameters live only in this window

Phase 2.3 Measurement Control is done when:

- XY scan parameters are clear and bounded by hardware limits
- simulation scan works
- constant-Z hardware raster works
- tapping scan measures contact Z at each XY point
- pause/stop behave correctly
- embedded line/topography views update point-by-point

Phase 2.4 Live Log is done when:

- it is useful for operator, service, and developer
- every hardware command/result is timestamped
- clear/download work
- logs include enough context to reproduce issues

Phase 2.5 Signal Windows is done when:

- external line mode windows can be opened for X+, X-, Y+, Y-
- external topography windows can be opened for X+, X-, Y+, Y-
- embedded Measurement views remain always visible
- all signal windows receive the same scan-point stream

## Most Important Design Rule Going Forward

Keep responsibilities separate:

- Main window: system control and safety.
- Z Scanner: all Z control and Z feedback.
- Measurement Control: XY raster, scan mode, scan progress, embedded line/topography.
- Live Log: operator/service/developer history.
- Signal Windows: visualization only.

This separation is the project’s current compass.

## New v0.2.11 Follow-Up Items

- Decide whether generated G-code should remain simple geometry or become slicer-profile aware.
- Add a visual G-code preview before export if time allows.
- Add a CR Touch manual trigger logger that records repeated M119 transitions and estimates repeatability.
- Add a hard software gate so CR Touch cannot become an active feedback source until a repeatability test passes.

## New v0.2.12 Follow-Up Items

- Make the G-code Studio preview visual inside the app, not only text.
- Add a PrusaSlicer launch shortcut if the local executable path is known.
- Add material/nozzle presets so extrusion-per-mm is not a hidden expert parameter.
- Add AI explanation text describing why the prompt resolved to the chosen concept.

## New v0.2.13 Follow-Up Items

- Replace the old “preview” idea with either a real plotted XY toolpath or no preview at all.
- Add a persistent chat-like transcript for multiple AI refinement rounds.
- Add material/nozzle presets before exposing this to real printing workflows.
- Add a button to open the saved file in PrusaSlicer if the path is configured.

## New v0.2.14 Follow-Up Items

- Add 3MF export if the project needs richer PrusaSlicer-ready metadata.
- Add direct launch/open-with-PrusaSlicer once the local executable path is configured.
- Add a small internal model sanity check before saving OBJ/STL: non-empty mesh, positive thickness, bed-fit warning.
- Keep raw G-code export behind clear expert wording; the normal path is OBJ/STL import and slicing in PrusaSlicer.

## v0.2.15 Phase 2.1 UI/Safety Close Update

- Main startup window is fixed to a compact Phase 2.1 System Control size: 430 x 620 px, roughly the requested small instrument panel format.
- System Control buttons and status area were enlarged so labels/status text remain visible.
- `File -> Exit` now routes through `request_safe_exit()`, which calls the same `closeEvent()` path as the window cross.
- Both exit paths run `safe_shutdown_before_close()`: stop active work, Safe Standby X125 Y105 Z120, then disconnect.
- If Safe Standby or disconnect fails, the software stays open instead of closing unsafely.

## v0.2.16 Academic AI Print Studio Update

- The Academic AI window is now organized as: build idea, printing parameters, discussion with AI, learning notes, actions, plan, hidden code.
- The workflow is intentionally simple: `Ask AI to Build`, `Discuss / Improve Plan`, `Agree to Final Plan`, `Generate Final File`, `Save Final File`.
- Added printing parameters: material, nozzle diameter, nozzle temperature, and bed temperature.
- Generated OBJ/STL/G-code text is hidden by default and can be shown with `Show Code`.
- Local learning notes are saved in `config/academic_ai_print_learning_notes.txt` and passed into future AI planning context.
- Learning notes do not train the external AI model; they make the next request smarter by providing project memory.

## v0.2.17 Phase 2.1 Connection State Update

- System Control connect button is now yellow `Connect` while idle.
- On click it immediately changes to yellow `Connecting...` while the hardware worker runs.
- After a successful connection payload it changes to green `Connected`.
- Disconnect remains red and is disabled until a connection is active.
- Connection visual state is payload-driven through `render_system_payload()`, so failed connects return to the safe yellow `Connect` state.

## v0.2.18 Academic AI Semi-Automatic Print Dialogue

- Academic AI Print Studio now starts with printer parameters before the AI build request.
- User can manually set all printer parameters or ask AI for parameter advice and click `Use AI Suggested Parameters`.
- The AI interaction is now a chat-style loop: user writes a message, clicks `Send to AI`, reviews the response, then repeats as often as needed.
- Chat history and turn count are included in AI context, with explicit support for 10+ refinement rounds before final confirmation.
- Final output flow is now `Confirm Final` -> `Create Code` -> `Save As`.
- Generated code remains hidden unless the user clicks `Show Code`.

## v0.2.19 Local/Open-Source AI Provider Layer

- Added provider strategy document: `D:\SPM_Prusa_Project\docs\SPM_AI_PROVIDER_STRATEGY.md`.
- `core\ai\academic_ai_client.py` now supports:
  - Academic AI provider
  - local OpenAI-compatible provider
  - safe local deterministic fallback
- Set `SPM_AI_PROVIDER=local` to route advisory calls to a local open-source model.
- Default local endpoint: `http://127.0.0.1:11434/v1/chat/completions`.
- Default local model: `qwen3-coder-next`.
- Added launchers:
  - `D:\SPM_Prusa_Project\spm_local_ai.bat`
  - `D:\SPM_Prusa_Project\spm_local_ai.ps1`
- Local AI is intended for self-development, scan logic, feature interpretation, auto-approach reasoning, log diagnosis, and code assistance.
- Motion remains deterministic and safety-gated. AI remains advisory-only.

## v0.2.20 Phase 2.1 Safe Close and Control Polish

- Added close-specific backend path `system_safe_standby_for_close()`.
- Close/Exit now attempts default Safe Standby X125 Y105 Z120 without requiring the prior Phase 2.1 diagnosis flag.
- Low-level standby still checks M114/count consistency, machine limits, and the health-motion gate before real movement.
- Added `Close Safely` button in Phase 2.1.
- Only Connect and Disconnect are colorful. Diagnosis, AI Error Correction, Safe Standby, and Close Safely use standard gray software buttons.
- Added Phase 2.1 communication log in the main panel for connection, diagnosis, standby, disconnect, and safe-close messages.
- Fixed dry-run standby payloads so they do not incorrectly turn the Connect button into green `Connected`.

## v0.2.21 Academic AI Print Studio Layout Polish

- Printer parameters are now compact in a three-column grid instead of a tall form.
- AI build request box is shorter.
- Interactive AI discussion transcript is taller and treated as the main workspace.
- Learning notes are compacted into a single row.
- Plan/code area now uses a vertical splitter so the operator can give more room to the plan or code view as needed.
- Chat transcript role labels are clearer and auto-scrolls to the latest message.

## v0.2.22 Academic AI Printable Geometry Upgrade

- Fixed the failure where a request for “hexagon with a half sphere in the center” only produced a simple hexagonal line frame.
- OBJ/STL generation now detects `sphere`, `half sphere`, `hemisphere`, `dome`, `ball`, and `half-ball` in the prompt/refinement notes.
- Hexagon model export now creates a continuous joined hexagonal frame instead of six separate bar-like segments.
- Dome requests add:
  - central hub
  - true hemispherical mesh
  - six connecting spokes from the hub to the hex frame
  - connected-corner print-oriented frame geometry
- OBJ exports include metadata:
  - `printable_joined_hex_frame`
  - `central_hemisphere`

## v0.2.23 Approach Advisor

- Added deterministic advisor module: `D:\SPM_Prusa_Project\core\ai\spm_approach_advisor.py`.
- Added `Approach Advisor` button to Phase 2.2 Z Scanner.
- Advisor checks:
  - system connected state
  - Z setpoint/contact limit
  - tapping range/search window
  - expected surface Z
  - approach speed
  - full retract Z
  - latest known Z
- Advisor classifies setup as `ready`, `caution`, or `blocked` and gives plain operator recommendations.
- Real foil/tapping scan now calls the advisor before starting and blocks incoherent Z search windows before hardware movement.
- This is the first step of the AI-assisted approach/measurement layer: deterministic safety logic first, AI explanation later.
