# Educational SPM v0.14.0 - Phase 9.6 Robust Executor

Date: 2026-06-12

## Scope

This checkpoint starts from the new project handoff and focuses only on Phase 9.6: robust command execution for the Phase 9 XY topography skeleton.

## Changed

- Replaced `tools/phase9_xy_10x10_topography_skeleton.py`.
- New script is dry-run by default and requires `--execute` for hardware motion.
- Added robust command executor for MK4S serial traffic.
- Handles `echo:busy: processing` without failing immediately.
- Uses longer timeouts for Z movement and `M400`.
- Avoids resetting the input buffer before every command.
- Logs raw serial traffic to `.txt`.
- Saves partial CSV after every completed point.
- Saves metadata on completion, failure, timeout, or interruption.
- Produces a PNG from partial data.
- Always attempts safety return: retract `Z=120`, then `X=125 Y=105`.
- Supports `--resume`.

## No-Motion Verification

Commands run:

```powershell
.\.venv\Scripts\python.exe -m py_compile tools\phase9_xy_10x10_topography_skeleton.py
.\.venv\Scripts\python.exe tools\phase9_xy_10x10_topography_skeleton.py --help
.\.venv\Scripts\python.exe tools\phase9_xy_10x10_topography_skeleton.py --size 2 --csv-out data\phase9_6_dryrun_probe.csv --png-out data\phase9_6_dryrun_probe.png --raw-log data\phase9_6_dryrun_probe_raw.txt --metadata data\phase9_6_dryrun_probe.metadata.json
.\.venv\Scripts\python.exe -m pytest -q
```

Result:

- Dry-run opened no serial port and moved no hardware.
- Full test suite passed: 131 tests.

Read-only hardware information exchange:

- Startup success: true.
- Port: COM5.
- Baudrate: 115200.
- `M115`: firmware identity confirmed.
- `M105`: temperature/status readback succeeded.
- `M119`: endstop readback succeeded; all min/max endstops open.
- `M114`: position readback succeeded at X 125.00, Y 105.00, Z 120.00.

## Recommended First Real-Motion Test

Only with operator supervision and clear hardware path:

```powershell
.\.venv\Scripts\python.exe tools\phase9_xy_10x10_topography_skeleton.py --execute --size 2
```

Do not run 10 x 10 until 2 x 2 and 3 x 3 have completed reliably.

## Backup

Edited files are backed up in:

`docs/versions/v0.14.0_phase9_6_robust_executor_2026-06-12/backup/`
