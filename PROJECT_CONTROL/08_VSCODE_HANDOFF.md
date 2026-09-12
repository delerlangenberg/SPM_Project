# SPM Prusa — Development Handoff

Updated: 2026-09-12

Workspace: `/srv/doro_lab_projects/apps/spm-prusa`
Interpreter: `.venv/bin/python`

Read `00_START_HERE.md`, `01_CURRENT_STATUS.md`, `02_ROADMAP.md`,
and `04_SAFETY_AND_USB_GATE.md` before continuing.

## Immediate work

Complete baseline review, dependency verification, commit, and recovery
checkpoint as specified in the current status.

Earlier conversational ML “Stage 3/4” labels are local task labels,
not authoritative roadmap stage numbers.
Advisor GUI integration has not been completed.

## Evidence and restrictions

Latest supplied results: 6 advisor tests and 42 full-suite tests passed.
The advisor uses operator-verified outcomes and plain JSONL history.
It does not authorize physical motion.

Do not run hardware testers, probe actuation, homing, Z approach,
motor-release commands, or physical scans during baseline closeout.
Historical device identities and coordinates are not live state.
The previous supervised-approach instructions are superseded.
