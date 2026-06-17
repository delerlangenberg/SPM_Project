# Two-Layer Educational SPM Development Roadmap

Date: 2026-06-12

## Principle

Build the software in two layers:

1. Hardware Test Layer: every hardware part is tested independently with clear commands, logs, limits, and safe return.
2. Measurement Layer: only after the hardware layer is trusted, combine parts into approach, line scan, raster scan, topography, and analysis.

## Layer 1 - Hardware Test Layer

### Phase HT1 - Simulated Command Bus

Status: complete.

- Simulated `POWER_ON`, `POWER_OFF`, `INFO`, `SAFE_STOP`.
- No real motion.
- Persistent command log.

### Phase HT2 - Real Read-Only Information Exchange

Status: started 2026-06-12.

Actions:

- `IDENTITY -> M115`
- `TEMPERATURE -> M105`
- `ENDSTOPS -> M119`
- `POSITION -> M114`
- `ALL -> all read-only actions`

Rules:

- No serial command is sent unless `--real` is used.
- No motion commands are allowed in this layer.
- Results are logged.

### Phase HT3 - Individual Axis Test Buttons

Status: backend/CLI started 2026-06-12.

Buttons/scripts:

- Read XYZ.
- Move X small step.
- Return X.
- Move Y small step.
- Return Y.
- Move Z up/down inside safe range.
- Safe center.
- Safe retract.

Each command must log:

- Command.
- Response.
- Timestamp.
- Before/after position.
- Success/failure.

Implemented CLI backend:

```powershell
.\.venv\Scripts\python.exe -m core.application.hardware_test_control_cli SAFE_CENTER
```

Dry-run is the default. Real movement requires:

```powershell
.\.venv\Scripts\python.exe -m core.application.hardware_test_control_cli SAFE_CENTER --execute
```

Available actions:

- `READ_POSITION`
- `SAFE_RETRACT`
- `SAFE_CENTER`
- `X_STEP_PLUS`
- `X_STEP_MINUS`
- `Y_STEP_PLUS`
- `Y_STEP_MINUS`
- `Z_STEP_UP`
- `Z_STEP_DOWN`

Safety:

- `SAFE_CENTER` retracts Z to `120` before XY movement.
- Small-step actions default to 5 mm.
- Confirmed firmware limits are enforced in software.
- Every dry-run or real execution logs to `logs/hardware_test_control_log.csv`.

### Phase HT4 - CR-Touch Z Probe Test Layer

Future phase after hardware is installed.

Steps:

- Manual probe trigger test.
- Electrical trigger read.
- Slow Z trigger approach.
- Repeatability measurement.

## Layer 2 - Measurement Layer

### Phase M1 - Single-Point Contact Height

Use known safe center first:

- X=125.
- Y=105.
- Z safe retract=120.

### Phase M2 - X-Line Skeleton

Use partial-save executor and small number of points.

### Phase M3 - Small XY Skeleton

Order:

- 2 x 2.
- 3 x 3.
- 10 x 10.

Do not run 50 x 50 or 100 x 100 until the command executor is stable.

### Phase M4 - Real Topography Workflow

Only after Z trigger/feedback is stable:

- Approach.
- Measure.
- Retract.
- Save.
- Resume/partial recovery.

### Phase M5 - Educational GUI

Only after CLI/backend behavior is stable:

- Main workstation.
- Hardware test panel.
- Z probe panel.
- Measurement panel.
- Analysis/report panel.

## Optional Academic AI Layer

AI is allowed only outside motion control:

- Summarize logs.
- Explain scan results.
- Generate reports.
- Help with handoff documentation.

AI is not allowed to:

- Send G-code.
- Start motion.
- Override limits.
- Decide safe/unsafe hardware state.

## Current Safe Next Step

Run read-only hardware information exchange:

```powershell
.\.venv\Scripts\python.exe -m core.application.hardware_information_cli ALL --real
```

Then, only with the operator supervising the hardware:

```powershell
.\.venv\Scripts\python.exe tools\phase9_xy_10x10_topography_skeleton.py --execute --size 2
```

## Verification Completed 2026-06-12

- Hardware information CLI dry-run passed with no serial connection.
- Real read-only `ALL --real` exchange passed on COM5.
- `M115`: Prusa MK4 firmware identity confirmed.
- `M105`: temperature/status readback succeeded.
- `M119`: all endstops reported open.
- `M114`: position readback succeeded at `X=125.00`, `Y=105.00`, `Z=120.00`.
- Full test suite passed: 136 tests.
- HT3 dry-run hardware test controls passed.
- Full test suite after HT3 passed: 143 tests.

### Phase HT3.1 - Hardware Test Console Interface

Status: complete in dry-run-first form 2026-06-12.

Interface:

```powershell
.\.venv\Scripts\python.exe -m core.application.hardware_test_console_gui
```

Purpose:

- Show read-only hardware information controls.
- Show supervised hardware test controls.
- Keep read-only commands separate from movement commands.
- Keep movement dry-run by default.
- Require `Enable supervised real motion` plus typed `SUPERVISED` plus confirmation popup before real movement.

Verification:

- Interface source compiled.
- GUI safety/source tests passed.
- Full test suite passed: 147 tests.

### Phase HT3.2 - User-Friendly Hardware Test Console

Status: complete 2026-06-12.

Reason:

- Operator feedback showed that the hardware did not react because the interface was still running motion commands in dry-run mode.
- The old wording made preview/dry-run behavior too easy to confuse with real execution.

Interface changes:

- Version updated to `v0.18.0`.
- Window title and header show `HT3.2 User-Friendly Hardware Test Console`.
- Added an `About` button with the current version and phase.
- Startup message now says preview mode is default and no motion is armed.
- Motion controls are split into:
  - `Preview Selected Command`
  - `EXECUTE SELECTED ON REAL HARDWARE`
- Quick hardware buttons are explicitly labeled as preview buttons.
- A large lock-state label shows whether real motion is locked or unlocked.
- If the operator presses execute while locked, the interface now shows a popup explaining why the hardware did not move.
- Real motion still requires:
  - check `Enable supervised real motion`
  - type `SUPERVISED`
  - press `EXECUTE SELECTED ON REAL HARDWARE`
  - confirm the warning popup while watching the MK4S

Verification:

- GUI source compiled.
- Focused GUI/control tests passed: 11 tests.
- Full project test suite passed: 147 tests.

### Phase HT3.3 - Guided Hardware Connection Check

Status: complete 2026-06-12.

Reason:

- Operator log showed repeated `MOTION PREVIEW` actions and one `MOTION LOCKED` action.
- The console correctly prevented movement, but read-only position checking was still mixed into the supervised motion panel.
- `READ_POSITION` is an `M114` status command and should be easy to run as a real safe check without unlocking motion.

Interface changes:

- Version updated to `v0.19.0`.
- Phase label updated to `HT3.3 Guided Hardware Connection Check`.
- Read-only information exchange now defaults to real read-only mode on COM5.
- Added connection status display.
- Added live XYZ position status display.
- Added `Run Real Connection Check`.
- Added `Read Current XYZ - Real Safe` in both the information panel and the motion panel.
- `READ_POSITION` executed from the real execute button now runs the read-only `M114` path, not the supervised motion path.
- Movement actions still require supervised unlock and confirmation.

Verification:

- GUI source compiled.
- Focused hardware GUI/control/information tests passed: 17 tests.
- Full project test suite passed: 148 tests.

### Phase HT3.4 - Smart Operator Console

Status: complete 2026-06-12.

Reason:

- Operator feedback: the interface still had too many visible buttons and felt slow/manual.
- The software should act more like a modern scientific instrument console: assess itself, summarize readiness, and recommend the next safe action.

Interface changes:

- Version updated to `v0.20.0`.
- Phase label updated to `HT3.4 Smart Operator Console`.
- Added a top-level `Smart Operator Console` as the main first screen.
- Added `Smart System Check` as the normal first operator action.
- Added local self-assessment for:
  - controller identity
  - temperature/status channel
  - endstop state
  - XYZ position parsing and limit check
- Added readiness state:
  - `READY_FOR_SUPERVISED_MOTION`
  - `CHECK_BEFORE_MOTION`
  - `NOT_READY`
- Added readiness score from 0 to 100.
- Added plain-language recommendation.
- Added self-assessment details.
- Expert hardware controls are hidden by default and revealed only with `Show expert hardware controls`.
- `Prepare Motion Test` opens expert controls and suggests a conservative first motion setup.

AI / Autonomy boundary:

- This phase adds local deterministic AI-style assessment.
- The Academic AI API can be added later for log summaries and reports.
- No online AI is allowed to directly send G-code, override safety limits, or start motion.

Verification:

- GUI and smart assessment source compiled.
- Focused GUI/control/information/smart-assessment tests passed: 21 tests.
- Full project test suite passed: 152 tests.

### Phase M0.1 - Main Workflow Initialize + Z Scanner

Status: complete 2026-06-12.

Reason:

- The smart hardware console is useful for troubleshooting, but the product main window must not feel like a diagnostic panel.
- The operator should start with one `INITIALIZE` button.
- After initialization passes, the system should show `SYSTEM READY` and make the Z scanner workflow the next clear step.

Main-window changes:

- Version updated to `v0.21.0`.
- Phase label updated to `Main Workflow - One Button Initialize + Z Scanner`.
- Main button is now `INITIALIZE`.
- Initialization now runs through `run_workstation_initialization`.
- One-button initialization performs:
  - scan-profile validation
  - MK4S no-motion hardware diagnostic
  - read-only identity/status/endstop/position assessment
  - local smart readiness scoring
  - dry-run Z scanner creation/connection
- If all checks pass, the main system banner changes to `SYSTEM STATUS: SYSTEM READY`.
- Main window now has a `Z Scanner / Approach` panel.
- Z scanner buttons promoted to main workflow:
  - `CREATE / CONNECT Z SCANNER`
  - `MANUAL Z MOVE`
  - `AUTO APPROACH`
  - `RETRACT Z`
- Z controls remain locked until initialization passes.

Safety boundary:

- Initialization still sends no movement commands.
- Current Z scanner is the safe dry-run/future hardware layer.
- Real motion remains disabled until explicitly enabled by the operator.

Verification:

- GUI and workstation initializer source compiled.
- Focused workflow tests passed: 47 tests.
- Hardware/smart support tests passed: 11 tests.
- Full project test suite passed: 155 tests.
