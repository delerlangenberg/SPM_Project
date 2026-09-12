# Migration History

## 2026-09-11 — Spark audit

Verified:

- NVIDIA DGX Spark;
- ARM64 Linux;
- NVIDIA GB10;
- CUDA 13;
- Python 3.12;
- Git available;
- approximately 3.4 TB free storage.

## Original SPM PC

Host:

`10.0.18.20`

User:

`spm`

Project root discovered:

`D:\SPM_Prusa_Project`

## Protected Windows recovery backup

`D:\SPM_Migration_Backups\SPM_PRE_SPARK_MIGRATION_20260911_104801`

Do not delete.

## Project history

Newest relevant milestones:

1. `v1.3.1.0_adaptive_object_release_20260731`
2. `v1.3.0.0_random_object_adaptive_verified_20260731`
3. `v1.3.0.0_stage2_surface_calibration_20260730`
4. `v1.3.0.0_stage2_centered_verified_20260730`

## Migration decision

Do not use the full historical 1.45 GB archive as the active Spark project.

Use only:

- latest release source;
- required verified runtime modules;
- verified tests;
- required calibration/data;
- essential documentation.

## Current Spark state

Canonical project:

`/srv/doro_lab_projects/apps/spm-prusa`

Git initialized.

Compilation currently passes.

Runtime validation currently blocked by missing NumPy.
