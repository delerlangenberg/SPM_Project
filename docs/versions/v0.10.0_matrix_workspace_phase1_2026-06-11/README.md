# Educational SPM v0.10.0 - MATRIX Workspace Phase 1

Date: 2026-06-11

## Purpose

This version starts a cleaner, MATRIX-inspired workstation layout for the Educational SPM project while preserving the current MK4S safety logic and directional raster scan work.

## Phase 1 Changes

- Added visible software versioning in the application title bar and top operator console.
- Added an About button with the active version, phase, build date, hardware target, and safety rule.
- Split the operator concept into separate launchable windows:
  - Measurement Console
  - XY Scanner
  - Z Regulation
  - Hardware Tests
  - Forward Image
  - Backward Image
  - Upward Image
  - Downward Image
- Reduced the main workstation shell so it fits normal monitor heights better.
- Connected directional image windows to loaded raster frames so each direction reports its sample count and line/topography summary.
- Kept the initialize-once workflow: initialization remains valid while the operator changes scan parameters until Power Off / Safe Park.

## Phase Plan

### Phase 1 - MATRIX-Style Shell

Build a monitor-safe main console with separate XY, Z, hardware, and image windows. Add visible versioning and About information.

### Phase 2 - Persistent Scientific Workspace

Move toward a true instrument workspace with remembered window positions, dock/restore behavior, and a cleaner distinction between operator status, hardware tools, and measurement controls.

### Phase 3 - Live Scan Engine

Replace blocking scan subprocess behavior with a non-blocking scan runner that streams each point/line to the GUI, supports pause/stop, and keeps CPU load low on different PCs.

### Phase 4 - Constant-Height SPM Feedback

Implement the real SPM feedback model: approach, regulate tip-sample distance, maintain constant interaction signal, and record Z/topography during forward/backward/upward/downward scans.

### Phase 5 - Fine Z Scanner and Sensor Integration

Add the future fine Z scanner hardware, sensor readback, calibration, limits, resolution reporting, and mode-specific STM/AFM-style configuration.

### Phase 6 - Measurement Records and Export

Save complete experiment metadata, hardware reports, scan settings, directional images, topography data, line profiles, and operator logs for reproducible educational measurements.

## Backup

The edited GUI source for this version is backed up in:

`docs/versions/v0.10.0_matrix_workspace_phase1_2026-06-11/backup/`
