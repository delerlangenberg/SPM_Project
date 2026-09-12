# SPM Prusa — Authoritative Project Control

## Canonical host

NVIDIA DGX Spark

## Canonical project

`/srv/doro_lab_projects/apps/spm-prusa`

## Objective

Build a modern scientific SPM platform based on the Prusa MK4S, running fully on Linux/DGX Spark.

Core targets:

- deterministic hardware control;
- probe and Z-feedback acquisition;
- scientific raster scanning;
- calibrated topography;
- quantitative surface analysis;
- uncertainty and provenance;
- ML measurement-quality assessment;
- anomaly and feature detection;
- adaptive ROI selection;
- adaptive scan planning;
- GPU-assisted scientific analysis.

## Recovery rule

Whenever context is lost, read:

1. `01_CURRENT_STATUS.md`
2. `02_ROADMAP.md`
3. `04_SAFETY_AND_USB_GATE.md`
4. `05_MIGRATION_HISTORY.md`

Work only on the CURRENT STAGE.

## Workflow

inspect
→ conclude
→ backup
→ controlled change
→ test
→ verify
→ document
→ advance
