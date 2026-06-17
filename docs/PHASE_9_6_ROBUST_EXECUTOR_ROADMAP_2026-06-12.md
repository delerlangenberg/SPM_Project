# Phase 9.6 Robust Scan Command Executor Roadmap

Date: 2026-06-12

## Current Goal

Build the project in two layers before returning to real SPM measurement:

1. Hardware test layer: power, initialize, read status, move individual parts under supervision, log every response, and always return to safe state.
2. Measurement layer: only after every hardware part is trusted, build approach, raster scan, line/topography capture, and real measurement workflows phase by phase.

## Why Phase 9.6 Exists

The 10 x 10 XY skeleton did not complete because the MK4 controller can emit repeated:

```text
echo:busy: processing
```

and delayed `ok` / `M114` responses during longer motion queues. The old script reset the input buffer before every command and only saved data after the whole scan, so failures could lose useful partial data.

## Safety Rules

- Do not run 50 x 50 or 100 x 100 scans.
- Do not leave the scanner unattended.
- Do not run real motion unless the MK4S path, foam, and Z clearance are visually confirmed.
- Always retract to `Z=120`.
- Always return XY to `X=125`, `Y=105`.
- Preserve partial data after every point.

## Phase 9.6 Implementation

Updated script:

`tools/phase9_xy_10x10_topography_skeleton.py`

New behavior:

- Dry-run by default; real hardware requires `--execute`.
- Supports small supervised shakedowns with `--size 2` or `--size 3`.
- Handles `echo:busy: processing` by continuing to wait until the command timeout.
- Uses longer timeouts for Z moves and `M400`.
- Does not reset the input buffer before every command.
- Writes raw serial traffic to a `.txt` log.
- Saves partial CSV after every completed point.
- Writes metadata with status, errors, timeout command, and last timeout lines.
- Generates a PNG from partial data even after interruption/failure.
- Runs safety return in `finally`: retract Z, then return XY to center.
- Can resume completed points with `--resume`.

## Recommended Next Test Sequence

### Step 1 - No Motion Dry-Run

```powershell
.\.venv\Scripts\python.exe tools\phase9_xy_10x10_topography_skeleton.py --size 2
```

Expected result:

- No serial port opened.
- No hardware movement.
- Planned points printed.
- Metadata written.

### Step 2 - Read-Only Hardware Check

Use existing initialization/read-only tools only:

- `M115`
- `M105`
- `M119`
- `M114`

Expected result:

- Controller identity confirmed.
- Current position returned.
- No motion.

### Step 3 - Supervised 2 x 2 Motion Shakedown

Only after the operator confirms the foam/path is clear:

```powershell
.\.venv\Scripts\python.exe tools\phase9_xy_10x10_topography_skeleton.py --execute --size 2
```

Expected result:

- 4 points only.
- CSV saved after every point.
- Raw serial log updated continuously.
- On failure or completion, Z returns to `120`, XY returns to `125,105`.

### Step 4 - Supervised 3 x 3 Motion Shakedown

Only if Step 3 is stable:

```powershell
.\.venv\Scripts\python.exe tools\phase9_xy_10x10_topography_skeleton.py --execute --size 3 --resume
```

Expected result:

- 9 points.
- Partial-save and resume behavior verified.

### Step 5 - 10 x 10 Skeleton

Only if Step 4 is stable:

```powershell
.\.venv\Scripts\python.exe tools\phase9_xy_10x10_topography_skeleton.py --execute --size 10 --resume
```

Expected result:

- 100 points maximum.
- Still fixed-contact-Z skeleton, not final SPM feedback.

## Two-Layer Software Roadmap

### Layer 1 - Hardware Test Console

Build first and fully validate:

- Power on / initialize.
- Read controller identity.
- Read temperatures/status.
- Read endstops.
- Read XYZ position.
- Move X only.
- Move Y only.
- Move Z only.
- Move to safe center.
- Retract Z.
- Power off / safe park.
- Every button writes command, response, timestamp, and status.

### Layer 2 - Measurement Console

Build only after Layer 1 is trusted:

- Select scan profile.
- Approach Z.
- Keep setpoint / constant interaction signal.
- Scan line forward/backward.
- Step Y.
- Accumulate topography.
- Save CSV/PNG/metadata.
- Pause/stop/resume.
- Safe park after completion or failure.

## Verification Completed This Pass

- Python compile passed for the Phase 9.6 script.
- Help command works.
- Dry-run `--size 2` works with no serial connection and no motion.
- Full test suite passed: 131 tests.
- Read-only hardware information exchange passed on `COM5 @ 115200`.
- Firmware identity: `Prusa-Firmware-Buddy 6.2.4+8909`, machine `Prusa-MK4`.
- Temperature/status readback succeeded with `M105`.
- Endstop readback succeeded with `M119`; all min/max endstops reported open.
- Position readback succeeded with `M114`: `X=125.00`, `Y=105.00`, `Z=120.00`.
