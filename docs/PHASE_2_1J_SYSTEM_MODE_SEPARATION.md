# Phase 2.1J System Mode Separation and Clean System Logs

## Purpose

This phase separates the simulation and hardware-read-only paths at the web UI level.

AI remains postponed to a later dedicated phase.

## Implemented

Main System now has an explicit Operating Mode selector:

- Simulation / Dry Run
- Hardware Read-Only - locked until explicit gate
- Real MK4S Motion - disabled

System ON uses the selected mode.

## Safety

Default mode remains dry-run.

Hardware read-only mode is visible but locked by default.

Real motion remains blocked.

This phase still does not:

- open serial,
- send G-code,
- move hardware,
- home axes.

## Log cleanup

System OFF and System CLOSE no longer repeat the dry-run startup command plan.

The dry-run plan is kept for System ON and System STATUS where it is useful.
