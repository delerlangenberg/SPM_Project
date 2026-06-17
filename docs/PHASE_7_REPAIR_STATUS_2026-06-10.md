# SPM Project Repair Status - 2026-06-10

## Completed Repair Slice

- Added a central workstation status model.
- Added a Phase 7 raster acquisition/readback layer.
- Wired GUI status panels to real state instead of passive placeholder labels.
- Kept the real-motion safety gate intact:
  - system check is required before real motion can be enabled
  - hardware scan remains disabled until real motion is enabled
  - confirmations remain required before critical actions
- Repaired direct script execution without requiring manual PYTHONPATH setup.
- Repaired dry-run behavior so dry-run scans generate synthetic raster CSV output without hardware motion.
- Kept plot generation backward-compatible with both `--color-map` and `--cmap`.
- Added no-motion hardware communication diagnostics.
- Wired GUI `INITIATE SYSTEM CHECK` to validate software and then query hardware communication before real motion can be enabled.
- Read and incorporated `SPM Workstation Project Overview.pdf` as the product brief for the long-term workstation goal.
- Added a formal acquisition-channel abstraction with the current safe simulated surface channel.
- Embedded generated raster plot preview into the GUI workstation feedback area.
- Added scan progress status support in the GUI.
- Added scan session metadata export for traceability.
- Read `ChatGPT - SPM.html`; it confirms the previous Phase 6.4A handoff and operator-first workflow direction.
- Read `Hardware/CRTouch_SPM_FINAL_Project.odt`; captured the CR-Touch contact Z-probe plan in code with real hardware disabled until the physical subsystem is ready.
- Added instrument-style GUI styling, tabbed measurement views, and an explicit SPM mode selector.
- Added a no-motion `READ MK4S POSITION` GUI action for checking the current Prusa stage position.
- Added visible axis-limit and resolution guidance beside scan input fields:
  - SPM-safe limits from project config
  - MK4S firmware soft limits from no-motion hardware query
  - resolution guidance for safe SPM development
- Added instrument-style line profile, XY topography text map, and Z/signal feedback readouts from raster CSV data.
- Added initialization-first GUI safety flow:
  - all action buttons are locked before `INITIATE SYSTEM CHECK`
  - initialization warning popup lists power, USB, surface-clearance, collision, and emergency-access checks
  - scan mode selector now uses `Scan mode` wording and opens a compact numeric limits window
- Added MK4S parking behavior for SPM-style shutdown:
  - `PARK MK4S` button is locked until initialization passes
  - parking retracts Z to 100 first, then moves XY to X1 Y1
  - initialized GUI close attempts the same parking sequence before exit
  - if parking fails, the GUI remains open for operator recovery
- Added mode-loaded SPM workflow controls:
  - selecting a scan mode loads scan area, XY speed, Z speed, Z dwell, approach, retract, and hardware/sensor expectations
  - GUI shows line-time, frame-time, and X-step estimates from the selected scan range and speed
  - Z controls now separate manual Z move, auto approach dry-run, and retract dry-run
  - scan commands now pass scan mode plus XY/Z feedrates into the verified CLI path
- Improved live scan readout:
  - line scan text now reports latest Y line, X sweep, point count, and Z/signal range
  - Z feedback text now reports live X/Y range, center signal, and min/max signal
- Refocused the GUI around the current real project boundary:
  - project title is now `Educational SPM - Prusa MK4S Workstation`
  - current installed hardware is stated as original Prusa MK4S X/Y/Z motion
  - fine Z scanner / sensor hardware is shown as future work, not active hardware
  - top-of-window operator workflow explains what a new user does first, second, third, through shutdown
  - current MK4S X/Y/Z position is shown as a persistent dashboard
  - approach/manual Z actions now show a training visual rather than implying active fine-Z hardware
- Cleaned and lightened the interface:
  - long workflow text moved to the Documentation tab
  - main workstation tab keeps only operational controls, live hardware parameters, and scan/Z feedback
  - scan setup, hardware tests, and Z/approach tools now open as separate utility windows
  - live raster, line, topography, and Z panels now use fixed dimensions
  - text previews compress long scan lines so high resolution does not resize the GUI
  - scan resolution is capped at 250 x 250 to avoid accidental heavy workloads
  - scan image inspection moved to a separate resizable `OPEN SCAN VIEWER` window
  - hardware parameters update on events instead of a fast polling loop
- Added professional shutdown gating:
  - `POWER OFF / SAFE PARK` disables real motion, disconnects dry-run Z, and parks the MK4S
  - `CLOSE SOFTWARE` remains disabled until safe power-off completes
  - window close is blocked until safe power-off is complete
- Added operation modes:
  - `DEMO SOFTWARE`: software-only scan flow
  - `HARDWARE TEST`: communication, position, parking, and hardware tools
  - `REAL MEASUREMENT`: standard Educational SPM measurement path
- Added directional SPM raster output:
  - forward trace, backward retrace, upward pass, and downward pass are recorded
  - 5 x 5 demo scan now records 100 directional samples, 25 per direction
- Preserved initialize-once workflow:
  - parameter changes after initialization do not require reinitialization
  - invalid parameter edits block scanning but keep the system initialized

## Verified

- Active test suite: 107 passed.
- Direct CLI dry-run creates synthetic raster output:
  - `data/phase7_dry_run_check.csv`
- Plot generation works:
  - `data/phase7_dry_run_check.png`
- Phase 7 readback layer loads the dry-run raster as a 5 x 5 / 25-point frame.
- Overview-progress dry run creates:
  - `data/overview_progress_check.csv`
  - `data/overview_progress_check.png`
- Metadata dry run creates:
  - `data/metadata_check.csv`
  - `data/metadata_check.metadata.json`
- MK4S no-motion limit query:
  - Firmware soft limits from `M211`: X -1..251, Y -4..211, Z 0..221
  - Current SPM safety envelope remains intentionally restricted to X 20..80, Y 20..80, Z 5..50
- Safe hardware demo on 2026-06-11:
  - Center move: PASS
  - Square move: PASS
  - Validated 5 x 5 hardware raster: PASS
  - Plot regenerated after restoring plotter defaults
- UI/live-readout dry run:
  - `data/ui_limit_live_check.csv`
  - `data/ui_limit_live_check.png`
  - Line scan, XY topography, and Z/signal text readouts verified.
- Sequential hardware test started with 3 x 3:
  - X 48..52, Y 48..52, Z 20
  - Resolution: 3 x 3
  - Result: PASS
  - Output: `data/hardware_3x3_check_2026_06_11.csv`
  - Plot: `data/hardware_3x3_check_2026_06_11.png`
- Official MK4S maximum positions tested:
  - X250: PASS
  - Y210: PASS
  - Z220: PASS
  - Z0 not auto-tested because it is collision-sensitive
  - Output: `data/original_mk4s_max_check_2026_06_11.csv`
- Official MK4S X/Y minimum positions tested:
  - X0: PASS
  - Y0: PASS
  - Output: `data/original_mk4s_xy_min_check_2026_06_11.csv`
- Config now separates:
  - `motion_limits`: official MK4S machine limits, X 0..250, Y 0..210, Z 0..220
  - `spm_safe_limits`: recommended SPM routine limits, X 20..80, Y 20..80, Z 5..50
  - `parking_position`: workstation park position, X1 Y1 Z100
- No-motion hardware communication check:
  - Serial candidates detected: COM1, COM3, COM5
  - Prusa MK4S communication on COM5: PASS
  - Firmware query `M115`: PASS, Prusa-Firmware-Buddy 6.2.4+8909
  - Position query `M114`: PASS, X54 Y54 Z20
  - Future fine Z scanner: WARN, not part of the current MK4S-original hardware test
- Mode-preset dry hardware check on 2026-06-11:
  - No-motion hardware communication: PASS
  - MK4S position readback: X1 Y1 Z100
  - `STM_DEMO` dry-run scan: PASS
  - Output: `data/stm_demo_mode_dry_test_2026_06_11.csv`
  - Plot: `data/stm_demo_mode_dry_test_2026_06_11.png`
  - Hardware movement: none

## Current Phase 7 Foundation

New modules:

- `core/application/workstation_status.py`
- `core/acquisition/channels.py`
- `core/acquisition/raster_stream.py`
- `core/acquisition/scan_session.py`
- `core/system/hardware_diagnostics.py`
- `core/system/hardware_profile.py`
- `core/z_control/crtouch_probe_plan.py`

New tests:

- `tests/test_workstation_status.py`
- `tests/test_acquisition_channels.py`
- `tests/test_raster_stream.py`
- `tests/test_scan_session.py`
- `tests/test_hardware_diagnostics.py`
- `tests/test_hardware_profile.py`
- `tests/test_crtouch_probe_plan.py`

New tools:

- `tools/run_hardware_communication_check.py`
- `tools/query_mk4s_machine_limits.py`

New docs:

- `docs/MK4S_MACHINE_LIMITS_AND_HARDWARE_TEST_2026-06-11.md`

## Next Recommended Slice

Add a non-blocking scan runner for the GUI so long dry-run/hardware scans do not freeze the window, then add real Z-controller communication checks once the external Z subsystem has confirmed wiring and port identity. After that, build the approach/engage workflow and replace simulated acquisition channels with real sensor channels as hardware becomes available.
