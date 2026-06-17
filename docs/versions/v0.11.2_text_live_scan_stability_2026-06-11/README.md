# Educational SPM v0.11.2 - Text Live Scan Stability Patch

Date: 2026-06-11

## Reason For Patch

The GUI still crashed after starting the demo scan. Windows reported the same native Qt crash:

- Faulting application: `pythonw.exe`
- Faulting module: `Qt5Core.dll`
- Exception: `0xc0000409`

Because the crash happened immediately after starting live scan rendering, this patch removes custom `QPainter`/`QPixmap` live drawing from the timer loop.

## Changes

- Version bumped to `v0.11.2`.
- Live line scan view now uses crash-safe text/ASCII rendering.
- Live topography view now uses crash-safe text/ASCII rendering.
- Removed `QPainter`, `QColor`, and `QPen` from the live scan path.
- Kept `QPixmap` only for static saved PNG preview/viewer functions.

## Verification

- Python compile: passed.
- GUI-focused tests: 40 passed.
- Full test suite: 111 passed.
- Timed live-demo probe completed cleanly without custom Qt painting.

## Next Step

Confirm the demo scan no longer crashes. If this stays stable, rebuild graphical line/topography visualization in a safer isolated widget or external image update path.

## Backup

Edited files are backed up in:

`docs/versions/v0.11.2_text_live_scan_stability_2026-06-11/backup/`
