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
