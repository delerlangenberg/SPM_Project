# Phase 2.2D - Smart Main System Connect / Disconnect

Status: complete and test-stable.

Validation:
- Web console tests: 37 passed.
- Full test suite: 203 passed.
- Real MK4S read-only connection was validated through the browser live hardware log.

Main System workflow:
- CONNECT
- Port dropdown: AUTO-DETECT / COM1-COM10 with APPLY.
- Mode dropdown: READ-ONLY / DRY-RUN with APPLY.
- SAFE RETRACT and DISCONNECT are side by side.
- CLOSE is not inside Main System.

Allowed read-only hardware commands:
- M115
- M105
- M119
- M114

Blocked in this phase:
- G0/G1 movement
- G28 homing
- G29 probing
- M17 motor enable
- M104/M109 hotend heating
- M140/M190 bed heating
- M500/M501/M502 printer writes
- hardware motion mode

Safety contract:
- Disconnect requires safe retract confirmation first.
- Browser/page close is guarded when connected.
- Safe retract is currently read-only confirmation of current Z position.

Next phase:
- Phase 2.2E should add controlled safe-retract Z motion with a strict movement allowlist.
