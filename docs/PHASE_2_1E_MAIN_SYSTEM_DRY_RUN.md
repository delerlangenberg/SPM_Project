# Phase 2.1E Main System Hardware-Start Shell and Dry-Run Mode

## Purpose

This phase returns to Phase 2.1 logically: the main system buttons must call a backend service, not only log placeholder messages.

## Implemented

Backend endpoints:

- `/api/system/status`
- `/api/system/on?mode=dry_run`
- `/api/system/off`
- `/api/system/close`
- `/api/system/dry-run`

Web GUI buttons now call the backend API:

- ON
- OFF
- STATUS
- CLOSE

## Safety

This phase is dry-run only.

No real MK4S command is sent.

No real motion is possible from this phase.

The dry-run startup plan only lists read-only checks planned for later hardware integration:

- `M115`
- `M119`
- `M105`
- `M114`

Forbidden in this phase:

- `G1`
- `G28`
- any real movement
- any automatic homing
- any direct serial write

## Logic

The intended operator flow is now:

1. System ON
2. System STATUS
3. Default Center
4. Z Approach
5. Measurement Start
6. Pause / Stop
7. System CLOSE / OFF

## Next phase

Phase 2.1F should discover and connect the existing safe hardware modules already in the project, but still only in read-only or dry-run mode first.

Suggested next step:

- locate existing MK4S backend
- locate existing visible move / read-only scripts
- connect `/api/system/status` to real read-only status if available
- keep real motion disabled
