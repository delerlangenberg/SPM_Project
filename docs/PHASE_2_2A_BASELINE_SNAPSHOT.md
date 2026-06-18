# Phase 2.2A Baseline Snapshot

Created: 2026-06-18 17:09:23

Latest commits:
be30ed2 Phase 2.1 remove legacy floating hardware log UI
6502a6c Phase 2.1 cleanup live log UI and ignore hardware logs
4ab1800 Phase 2.1 closeout real hardware safe controls

Git status:
?? docs/PHASE_2_2_ROADMAP_CONTROLLED_REAL_SCAN.md

Phase 2.2A purpose:
Identify the current scan/raster architecture before adding real hardware scan execution.

Hardware-safe baseline:
- Current hardware connection: COM5, Prusa MK4S.
- Last verified safe Z: 150 mm.
- Real Safe Retract target: Z=150 mm.
- 50% movement test passed after timeout adjustment.
- Phase 2.2 must keep scan motion above safe Z until contact/probe logic is explicitly added.
