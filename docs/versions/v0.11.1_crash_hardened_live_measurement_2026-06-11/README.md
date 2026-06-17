# Educational SPM v0.11.1 - Crash-Hardened Live Measurement

Date: 2026-06-11

## Reason For Patch

The v0.11.0 GUI crashed after running briefly. Windows recorded a Qt crash:

- Faulting application: `pythonw.exe`
- Faulting module: `Qt5Core.dll`
- Exception code: `0xc0000409`

The plain GUI startup stayed alive during probing, and the live-scan probe completed under Python `faulthandler`. This patch hardens the runtime shutdown/interruption path.

## Changes

- Version bumped to `v0.11.1`.
- Added `stop_live_scan_runtime(reason)` to stop the live scan timer safely.
- Power-off now stops any active live scan before safe parking/deinitialization.
- Window close now stops the live scan timer before enforcing the safe power-off gate.
- Relaunched the GUI with the Measurement window visible.

## Hardware Self-Test Result

Safe no-motion hardware communication self-test:

- Overall: PASS
- MK4S detected on COM5 at 115200 baud.
- Firmware query succeeded.
- Position query succeeded: X 1.00, Y 1.00, Z 100.00.
- No motion was commanded.

## Verification

- GUI-focused tests: 40 passed.
- Full suite: 111 passed.
- Live-scan probe with automatic start and timed exit completed with exit code 0.

## Backup

Edited files are backed up in:

`docs/versions/v0.11.1_crash_hardened_live_measurement_2026-06-11/backup/`
