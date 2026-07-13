# SPM Prusa Project

Active Scanning Probe Microscopy prototype and operator software using a Prusa MK4S as the motion platform.

## Source Of Truth

The authoritative project root is:

`D:\SPM_Prusa_Project`

Older `C:\SPM_Project` references in historical notes are no longer the active working location.

## Current Status

- Prusa MK4S is the active motion backend
- Operator software, hardware gating, and scan workflows live in this repository
- Hardware, roadmap, and AI advisory documents are consolidated under `docs`
- Hardware planning material is kept under `Hardware`
- Tests, legacy tests, and backups are preserved in this tree

## Main Areas

- `core` - application logic, scan flow, hardware abstraction, AI, web, and Z control
- `web` - operator console frontend
- `docs` - roadmap, handoff, logs, hardware bring-up, and operator guidance
- `Hardware` - physical build and sourcing documentation
- `tests` - active test suite
- `tests_legacy` - preserved older tests and fixtures

## Launch

Use PowerShell:

```powershell
cd D:\SPM_Prusa_Project
.\spm.bat
```

For local AI launch:

```powershell
cd D:\SPM_Prusa_Project
.\spm_local_ai.bat
```

## Setup

```powershell
cd D:\SPM_Prusa_Project
$env:PYTHONPATH = 'D:\SPM_Prusa_Project'
```

## Main Documents

- `docs\PROJECT_OVERVIEW.md`
- `docs\SPM_OPERATOR_SOFTWARE_USER_GUIDE.md`
- `ROADMAP_SPM_PRUSA.md`
- `docs\SPM_PROFESSIONAL_PHASE_ROADMAP.md`

## Important Notes

- Treat this D-drive project as the only active edit target.
- Some related PDFs, DOCX files, and live logs still exist in `C:\Users\SPM\Downloads` and should be reviewed before import.
- Historical zip bundles in the project root are preserved as local recovery checkpoints.

## Consolidation Note

See `docs\PROJECT_CONSOLIDATION_2026-07-13.md` for the latest inventory and recommendations.


