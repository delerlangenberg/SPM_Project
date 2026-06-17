# Phase 2.3C Stable Menus, New-Tab Views, and Stronger Measurement Control

## Purpose

This phase improves the operator logic after testing Phase 2.3B.

## Changes

### Stable menus

The top menu now behaves more like normal software:

- View
- Tools
- Open
- About

Dropdowns are click-stable instead of hover-only.

### New-tab support

View windows can now be opened in a separate browser tab for future two-monitor work.

Supported new-tab views:

- Line Mode
- Topography
- Live View
- System Status
- Scan Setup

### Non-blocking main page

The normal in-page windows remain non-blocking and several can stay open at once.

### Stronger measurement workflow

Measurement now follows:

1. Default Center
2. Z Approach
3. Measurement Start
4. Pause / Stop

Measurement Start is blocked unless Default Center and Z Approach are complete.

Pause and Stop now interrupt the raster loop using a run token so delayed line results are discarded instead of continuing to accumulate after Stop.

## Next phase

Phase 2.4 should connect one backend module at a time:

1. real/default XY center service,
2. Z readback service,
3. Z approach service,
4. scan executor dry-run,
5. export pipeline.
