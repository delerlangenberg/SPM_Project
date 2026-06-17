# Phase 2.1H Connect System STATUS to Existing Hardware Information Layer

## Purpose

This phase connects the web System STATUS backend to the existing project hardware information layer.

AI integration is postponed to a later dedicated phase.

## Implemented

New web adapter:

- `core/web/hardware_status_adapter.py`

It reads existing safe definitions from:

- `core.system.hardware_information_exchange`

Expected read-only actions:

- `IDENTITY -> M115`
- `TEMPERATURE -> M105`
- `ENDSTOPS -> M119`
- `POSITION -> M114`

## Safety

This phase is still dry-run and read-only planning only.

The web adapter does not:

- open serial,
- send G-code,
- move hardware,
- home axes,
- perform Z approach.

## System STATUS now returns

- `simulation_status`
- `hardware_information_status`
- `hardware_information_plan_valid`
- `safety.serial_opened = false`
- `safety.gcode_sent = false`

## Next phase

Phase 2.1I should add an explicit hardware-read-only gate.

Goal:

- simulation mode still works,
- hardware status mode can be selected,
- real serial read-only checks are still blocked unless explicitly enabled,
- no motion commands are ever allowed from this status path.
