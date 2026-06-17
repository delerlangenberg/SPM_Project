# Phase 2.1I Status-in-Log Only and AI Postponement

## Purpose

This phase cleans the operator workflow after testing the system-control and hardware-information status bridge.

## Changes

### System STATUS

System STATUS no longer opens a new window.

It now:

- calls `/api/system/status`,
- writes the result summary into the live log,
- keeps the internal status JSON updated for debugging,
- does not interrupt the main operator page.

### View menu

View now contains measurement/monitoring views only:

- Line Mode
- Topography
- Z Feedback Live View

System Status is not duplicated there because the main STATUS button and live log are enough.

### Tools menu

Tools now contains scan tools only:

- Check Scan Profile
- Reset Raster

### AI

Visible AI UI is postponed.

The backend stubs can remain in the codebase, but the GUI does not present AI as an active tool during the simulation/hardware stabilization phase.

AI should later receive its own dedicated phase, for example:

- AI advisory for scan planning,
- AI support for printing-code generation,
- AI support for Z approach strategy,
- AI support for scanned-structure interpretation,
- AI support for scanning probe and hardware/software development.

## Safety

No serial connection.

No G-code sent.

No motion.

Current focus remains:

- simulation path,
- hardware-information path,
- safe dry-run bridge.
