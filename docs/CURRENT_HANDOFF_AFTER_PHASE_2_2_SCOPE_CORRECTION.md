# SPM Prusa MK4S Project Handoff

Created: 2026-06-18 19:12:56

Use this document to continue the project in a new chat.

## Project Identity

Project path:
D:\SPM_Prusa_Project

Hardware:
- Prusa MK4S used as an educational SPM/AFM/STM-style scanner motion platform.
- COM port used in tests: COM5.
- Current safe center used in tests: X125 Y105.
- Current safe Z after retract tests: Z80 or Z150 depending on last test state.
- Do not assume homed position unless M114 confirms it.

Project goal:
Build a safe educational scanning probe microscope demonstrator. The Prusa MK4S provides large-scale X/Y/Z motion. The software must separate:
1. Z-scanner approach/control.
2. XY raster scan measurement.
3. Future real sensor feedback.

Current git state before this handoff:
- Latest important commit: c4be0ab Phase 2.2 separate Z scanner scope from XY scan staging.
- Full tests passed: 210 passed.

## Completed Phase 2.1

Phase 2.1 is closed.

Confirmed:
- Web console launches correctly.
- SPM LIVE LOG - API / HARDWARE works inside the UI.
- Old floating hardware-log buttons were removed.
- Hardware logs are ignored by git.
- Real hardware read-only connection works.
- Short health test works.
- 50 percent health test works.
- Real safe retract works.
- No homing, heating, probing, or raster scan is enabled as uncontrolled motion.

Important commits:
- be30ed2 Phase 2.1 remove legacy floating hardware log UI
- 6502a6c Phase 2.1 cleanup live log UI and ignore hardware logs
- 4ab1800 Phase 2.1 closeout real hardware safe controls

## Corrected Phase Structure

Important correction:
Phase 2.2 is Z-scanner only.

Phase 2.2 scope:
- Z position readout.
- Z range display.
- Surface Z setting.
- Clearance above surface in micrometers.
- Fast approach guard distance.
- Fine Z step size.
- Retract Z.
- Live Z feedback window.
- Software-position Z approach.
- No XY raster scan.

Phase 2.3 scope:
- X/Y scan size.
- X/Y resolution.
- Raster directions X+, X-, Y+, Y-.
- Line accumulation.
- Topography image building.
- Scan-time estimation.
- CSV/image output.

The XY scan planner and raster preview already exist, but they are now classified as Phase 2.3 staging and must not be treated as active Phase 2.2 work.

## Phase 2.2A Z Approach Findings

Controlled coin/foam test:
- User placed a 1 euro coin on foam near expected surface height around Z55 mm.
- Script moved to X125 Y105.
- Z approached downward in controlled steps.
- Hard floor was Z55 mm.
- Script retracted to Z80 mm.
- M119 reported all endstops open during approach.
- Result: NO_M119_CONTACT_TRIGGER_BEFORE_FLOOR.

Conclusion:
- Z approach motion and retract are safe.
- M119 is not a verified contact detector.
- Do not claim automatic contact detection using M119.
- Current auto-approach is software-position approach only.

Future real contact/STM feedback requires one verified channel:
- external contact sensor,
- exposed Prusa loadcell/probe signal,
- STM current threshold,
- analog/digital sensor,
- or another validated feedback source.

Software-position approach model:
- User declares expected surface Z.
- User declares target clearance above surface in micrometers.
- System computes target Z.
- System rounds target Z to Prusa Z executable resolution.
- From observed M114:
  - X/Y scale: 100 counts/mm = 10 µm/count.
  - Z scale: 400 counts/mm = 2.5 µm/count.

## Important Current Files

Z-scanner / hardware files:
- tools\phase_2_2a_auto_approach_coin.py
- tools\phase_2_2a_software_auto_approach.py
- core\web\mk4s_health_motion.py
- core\web\system_control.py
- core\web\operator_console_server.py
- web\operator_console\z_live.js
- web\operator_console\reliable_live_log.js

Phase correction files:
- docs\PHASE_SEPARATION_2_2_Z_AND_2_3_XY_SCAN.md
- docs\PHASE_2_2_ROADMAP_CONTROLLED_REAL_SCAN.md

Phase 2.3 staging files:
- core\web\spm_scan_planner.py
- core\web\spm_scan_plan_api.py
- web\operator_console\scan_plan_ui.js
- web\operator_console\scan_preview_ui.js
- docs\PHASE_2_3A_XY_SCAN_MEASUREMENT_MODEL.md
- tests\test_spm_scan_planner.py
- tests\test_spm_scan_plan_api.py

Important UI rule:
- scan_plan_ui.js and scan_preview_ui.js should not be loaded in active Phase 2.2 UI.
- They are for Phase 2.3 staging.
- Phase 2.2 UI should focus on Z-scanner settings and live Z feedback only.

## Next Work To Do

Next phase to implement:
Phase 2.2C or next corrected Z-scanner step.

Immediate next goals:
1. Build a Z-scanner parameter panel in the web UI.
2. Show:
   - current Z mm,
   - Count Z,
   - Z resolution 2.5 µm/count,
   - declared surface Z,
   - target clearance µm,
   - computed target Z,
   - rounded executable target Z,
   - fast guard distance,
   - fine step size,
   - retract Z.
3. Add a live Z feedback window.
4. Add a safe software-position Z approach button.
5. Keep no XY raster scan in Phase 2.2.
6. Keep no real contact claim until a sensor feedback channel is verified.

Testing expectations:
- Full tests currently: 210 passed.
- Use:
  .\.venv\Scripts\python.exe -m pytest -q

Safety rules:
- No homing.
- No heating.
- No firmware writes.
- No blind lowering below declared floor.
- No XY raster scan during Phase 2.2.
- Real hardware movement must require explicit confirmation.
- Always read M114 before Z motion.
- Always retract to a safe Z after approach.

---

# Paste This Into A New Chat

Continue the SPM Prusa MK4S Educational Scanner project.

Project path:
D:\SPM_Prusa_Project

Use my preferred work format:
1. Roadmap step
2. Run this code
3. Check outcome / expected result

Important:
- Keep code blocks small.
- Do not use long here-strings unless split into sections.
- Do not commit until a phase milestone is complete.
- Backup/commit only at full phase milestones.

Current state:
- Phase 2.1 is closed.
- Phase 2.2 was corrected to be Z-scanner only.
- Phase 2.3 is reserved for XY raster scan measurement.
- Latest important commit: c4be0ab Phase 2.2 separate Z scanner scope from XY scan staging.
- Full tests passed: 210 passed.

Hardware:
- Prusa MK4S on COM5.
- Safe center used: X125 Y105.
- M114 confirmed Z feedback works.
- M119 did not detect contact in coin/foam test.
- Therefore M119 must not be used as contact feedback.

Phase 2.2 scope:
- Z scanner settings.
- Live Z feedback.
- Software-position Z approach.
- Surface Z and clearance in micrometers.
- Fast guard distance and fine step size.
- Safe retract.
- No XY raster scan.

Phase 2.3 staging exists but should not be active in Phase 2.2:
- spm_scan_planner.py
- spm_scan_plan_api.py
- scan_plan_ui.js
- scan_preview_ui.js
- PHASE_2_3A_XY_SCAN_MEASUREMENT_MODEL.md

Next task:
Build the real Phase 2.2 Z-scanner parameter panel and live Z feedback window in the web UI. Do not re-enable XY scan planner UI yet.
