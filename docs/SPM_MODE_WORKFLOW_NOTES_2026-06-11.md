# SPM Mode Workflow Notes - 2026-06-11

## Sources Reviewed

- Uploaded guide: `C:\Users\SPM\Downloads\spm_guide_0829_05_166.pdf`
- Operator log: `C:\Users\SPM\Downloads\0830_operator_log.txt`
- FemtoScan online manual: `http://www.nanoscopy.net/manual/en/`

## Workflow Applied

The GUI now follows a practical SPM sequence:

1. Select scan mode.
2. Load mode-specific hardware, sensor, Z-control, scan-range, and speed presets.
3. Let the user adjust X/Y scan range and resolution.
4. Show estimated line time, frame time, and X step size.
5. Configure the original MK4S Z height/clearance plus dry-run approach/retract training settings.
6. Run initialization and no-motion hardware communication checks.
7. Allow dry-run scanning, then optionally real hardware scan after arming and confirmation.

## SPM Behavior Captured

- Raster scanning is X/Y line-by-line.
- X is treated as the fast-scan direction and Y as the slow-scan direction.
- Resolution controls the number of samples per line and number of scan lines.
- Current installed hardware is the original Prusa MK4S X/Y/Z motion system.
- Z behavior depends on the selected mode:
  - STM-style work is modeled as constant-current feedback in software.
  - AFM contact-style work is modeled as constant-force feedback in software.
  - Fine SPM Z scanner and sensor hardware are future add-ons, not active in the current MK4S-original tests.
- Z approach and retract are separate operator steps from X/Y raster scanning.
- Closing the GUI after initialization parks Z first, then XY.

## Dry Test Result

No-motion hardware communication check:

- Result: PASS
- MK4S controller: COM5
- Firmware: Prusa-Firmware-Buddy 6.2.4+8909
- Position readback during check: X1 Y1 Z100
- Future fine Z scanner: WARN, dry-run training only until the later subsystem is connected

Mode-preset dry scan:

- Mode: `STM_DEMO`
- Scan area: X49..51, Y49..51, Z20
- Resolution: 5 x 5
- XY speed: 300 mm/min
- Z speed: 60 mm/min
- Output: `data/stm_demo_mode_dry_test_2026_06_11.csv`
- Plot: `data/stm_demo_mode_dry_test_2026_06_11.png`
- Hardware movement: none

Live readout verified:

- Latest Y line is shown.
- X sweep range is shown.
- Z/signal range is shown.
- Z feedback summary includes live X/Y range and center signal.

## Professional Operator Model Added

The GUI now keeps the main workstation clean and puts the full workflow in the Documentation tab:

1. Prepare the sample/object and clear the MK4S.
2. Initialize communication and read current MK4S position.
3. Select measurement mode.
4. Define XY scan area on the object.
5. Set MK4S Z height/clearance.
6. Run dry-run scan and inspect line/topography/Z feedback.
7. Enable real motion only for supervised hardware testing.
8. Close/deinitialize so the software parks Z100 first, then X1 Y1.

For a first training object, the GUI describes a 100 x 100 mm object and recommends selecting a smaller XY scan window inside it before attempting large-area mapping.

## Interface Cleanup and Performance Policy

- The main workstation tab keeps controls, live hardware parameters, current MK4S position, Z approach preview, and scan feedback visible.
- Long workflow notes live in the Documentation tab instead of consuming main interface space.
- The main workstation is now a compact console; scan setup, hardware tests, and Z/approach tools open as separate utility windows.
- The operator console uses two rows so core buttons stay visible on smaller displays.
- The workstation tab is scroll-safe; if a PC display is short, controls remain reachable instead of being clipped.
- The default window size is calculated from the monitor's available area and capped to a compact size.
- Live line/topography/Z panels have fixed dimensions so changing scan range or resolution does not resize the rest of the software.
- Text previews are compressed to a fixed width for display; full-resolution data remains in the CSV and plotted image.
- Maximum accepted scan resolution is 250 x 250 to avoid accidental heavy workloads on weaker PCs.
- Scan image inspection is available through `OPEN SCAN VIEWER`, a separate resizable window.
- The application uses event-driven hardware-parameter updates instead of a fast polling loop, reducing CPU and serial-port load.

## Operation Modes

- `DEMO SOFTWARE`: tests the software scan flow with no hardware motion.
- `HARDWARE TEST`: opens hardware communication, position, park, and motion-safety tools.
- `REAL MEASUREMENT`: standard Educational SPM measurement path; initialize once, complete Z approach, then scan.

Initialization is intended to be done once per session. Changing scan parameters after initialization does not require reinitialization; invalid parameters only block the scan until corrected.

## Directional Raster Model

The raster data model now records all normal SPM directions over the scan area:

- forward X trace
- backward X retrace
- upward Y pass
- downward Y pass

For a 5 x 5 scan, this produces 100 directional samples: 25 per direction. The topography image uses the sampled height/signal at each X/Y point, while the line/Z summaries report direction counts.

## Shutdown Policy

- `POWER OFF / SAFE PARK` is the required deinitialization action.
- It disables real motion state, disconnects the dry-run Z trainer, and parks the MK4S if initialization was completed.
- `CLOSE SOFTWARE` remains disabled until power-off/safe-park completes.
- The window close button is blocked until safe power-off is complete.
- After a completed real hardware scan, the GUI requests a post-scan safe park: Z first, then XY.
