# Project Consolidation Report

Date: 2026-07-13

## Summary

The active and most advanced Scanning Probe Microscopy project on this PC is already located at `D:\SPM_Prusa_Project`.

This location contains:

- the active software tree
- operator documentation
- hardware planning documents
- test suites
- hardware logs
- local backup zip bundles

The main cleanup gap was documentation drift: the root README still described the old `C:\SPM_Project` location.

## What Was Confirmed

- `D:\SPM_Prusa_Project` exists and is the active project root
- the project already includes mature roadmap, operator, hardware, and architecture documentation
- the old `C:\SPM_Project` path referenced in historical docs is not present on this PC
- additional backup copies exist on `D:\SPM_Prusa_Project_Backups` and `D:\Backup_SPM`
- several related files still live outside the project, mainly in `C:\Users\SPM\Downloads`

## Additional Related Project Copies

These locations appear to be backup or historical working copies related to the same project family:

- `D:\SPM_Prusa_Project_Backups\phase0_clean_20260616_113050`
- `D:\SPM_Prusa_Project_Backups\phase1_stabilized_20260616_165428`
- `D:\Backup_SPM\SPM_Project`
- `D:\Backup_SPM\Doro_Lab_Projects\SPM_Project`
- `D:\Backup_SPM\SPM_Project_GitHub_Version`

These should be treated as reference or recovery copies, not as active edit targets.

## Main Project Structure

- `core` - modular application, scan, hardware, AI, and control logic
- `web` - operator console UI
- `docs` - handoff notes, roadmap, logs, operator guide, and design notes
- `Hardware` - build planning and sourcing documents
- `tests` and `tests_legacy` - active and preserved validation suites
- `backups` and root zip bundles - recovery snapshots

## External Related Files Found

The following files appear related and are outside the active project tree:

- `C:\Users\SPM\Downloads\spm_live_log_2026-06-22T07-19-14-322Z.txt`
- `C:\Users\SPM\Downloads\spm_live_log_2026-06-22T07-10-04-842Z.txt`
- `C:\Users\SPM\Downloads\spm_live_log_2026-06-22T06-43-48-279Z.txt`
- `C:\Users\SPM\Downloads\spm_live_log_2026-06-19T12-31-47-086Z.txt`
- `C:\Users\SPM\Downloads\spm_live_log_2026-06-19T12-24-11-342Z.txt`
- `C:\Users\SPM\Downloads\spm_live_log_2026-06-19T12-12-58-137Z.txt`
- `C:\Users\SPM\Downloads\spm_live_log_2026-06-19T12-04-50-865Z.txt`
- `C:\Users\SPM\Downloads\spm_live_log_2026-06-19T12-00-57-513Z.txt`
- `C:\Users\SPM\Downloads\spm_live_log_2026-06-19T11-59-03-713Z.txt`
- `C:\Users\SPM\Downloads\spm_hardware_live_log_WEB_20260618064602_237BB2.txt`
- `C:\Users\SPM\Downloads\spm_hardware_live_log_WEB_20260618064602_237BB2 (1).txt`
- `C:\Users\SPM\Downloads\MK4S Specification Settings for the SPM Prusa Scanner.pdf`
- `C:\Users\SPM\Downloads\SPM Prusa MK4S Educational Scanner Project Handoff.pdf`
- `C:\Users\SPM\Downloads\SPM Prusa Project Handover Status.pdf`
- `C:\Users\SPM\Downloads\CRTouch_SPM_FINAL_Project.docx`
- `C:\Users\SPM\Downloads\CRTouch_SPM_FULL_Project.docx`
- `C:\Users\SPM\Downloads\CRTouch_SPM_Project.docx`
- `C:\Users\SPM\Downloads\CRTouch_SPM_Concept-Shape.step`
- `C:\Users\SPM\Downloads\crtouch_spm_probe_concept.stl`

## Likely Non-Project Or Low-Priority Items

These are Prusa-related but do not appear to be core SPM project assets:

- PrusaSlicer installer executables in Downloads
- phone stand `.3mf` and `.stl` files in Downloads

They may be useful workstation tooling or unrelated printer files, but they should not be treated as primary SPM project inputs.

## Recommended Clean Working Rule

Use `D:\SPM_Prusa_Project` as the single clean working location for all future edits.

Recommended operator rule:

1. New code, docs, and logs go into `D:\SPM_Prusa_Project` only.
2. External files in Downloads are reviewed before import.
3. Backup trees under `D:\SPM_Prusa_Project_Backups` and `D:\Backup_SPM` remain read-only unless a recovery diff is needed.
4. Only import files that add unique value or preserve traceability.
5. Keep casual printer assets and installers outside the project tree.

## Suggested Next Cleanup Pass

If you want the tree to become stricter, the next safe step is a manual import review for the external files above.

Recommended destination ideas inside the project:

- live logs -> `docs\hardware_logs\external_imports`
- handoff PDFs -> `docs\versions` or `docs\handoff`
- CR-Touch CAD and planning files -> `Hardware`

This report intentionally does not move files automatically, to avoid overwriting project history or importing duplicates without review.