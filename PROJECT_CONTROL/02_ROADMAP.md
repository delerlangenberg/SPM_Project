# SPM Prusa — Authoritative Roadmap

## Stage 0 — Protect old system
**COMPLETE**

- identify SPM PC;
- identify project history;
- create protected recovery backup;
- preserve old Windows installation.

## Stage 1 — Select software baseline
**COMPLETE**

- identify latest v1.3.1.0 release;
- identify verified support milestones;
- selectively migrate only useful source;
- establish Spark project root.

## Stage 2 — Native Linux runtime
**COMPLETE — 2026-09-11**

Completion criteria:

- native ARM64 Python environment: PASS;
- dependencies installed: PASS;
- compile passes: PASS;
- canonical tests pass: PASS;
- simulation smoke test passes: PASS;
- application launches without hardware: PASS;
- default state is simulation/hardware locked: PASS.

## Stage 3 — Freeze Spark baseline
**COMPLETE — subject to verified recovery checkpoint**

- Exact Python package snapshot and offline rebuild: PASS.
- Rebuilt environment: 42 canonical tests passed.
- Temporary source backups retired; legacy tools retained as source.
- Handbook files included directly in the parent repository.
- Clean source baseline committed: `53f3b91`.
- Recovery location and activation condition: see current status.

## Stage 4 — USB migration to Spark
**COMPLETE — activated by the recovery marker in current status**

- MK4S and Arduino enumerated and identified by serial number.
- Persistent aliases and account permissions verified.
- Udev configuration captured.
- OS inspection only; no serial communication or motion.
- Evidence: `14_STAGE_4_USB_VERIFICATION.md`.

## Stage 5 — Read-only hardware communication
**COMPLETE — 2026-09-12**

- identity: PASS (`Prusa-MK4`, `SPM_PROBE_MEGA2560`);
- firmware: PASS (`Buddy 6.2.4+8909`, `0.8.7-fast-tap`);
- temperature: PASS (`M105` telemetry received);
- endstop/probe state: PASS (`M119` all axes open, trigger_raw false);
- XYZ position: PASS (`M114` parsed);
- Arduino identity/status: PASS (self-test PASS, actuation locked);
- disconnect/reconnect: PASS (clean serial close);
- timeout handling: PASS;
- zero motion / zero writes verified: PASS.

Evidence: `16_STAGE_5_READONLY_VERIFICATION.md`.

## Stage 6 — Deterministic hardware safety gate
**COMPLETE — 2026-09-12**

- coordinate limits: PASS ($X, Y \in [20, 80]\,\text{mm}$);
- safe Z floor: PASS ($Z_{\min} = 120.0\,\text{mm}$ hard limit);
- probe state & watchdog: PASS ($250\,\text{ms}$ freshness deadline, non-recovering fault latch);
- fault handling & abort: PASS (immediate halt, cancellation, operator ack required);
- interlocks & central authority: PASS (`DeterministicHardwareSafetyGate`);
- command policy: PASS (absolute rejection of `G28`/`G29`/heaters).

Evidence: `17_STAGE_6_SAFETY_GATE_VERIFICATION.md`.

## Stage 7 — Controlled motion commissioning
**COMPLETE — 2026-09-12**

- minimal-risk motion execution through `DeterministicHardwareSafetyGate`: PASS;
- target coordinates within safe scan envelope ($X, Y \in [20, 80]\,\text{mm}$, $Z \ge 120\,\text{mm}$): PASS;
- Arduino Mega telemetry stream verified: PASS;
- position confirmation via `M114`: PASS;
- emergency stop / abort interlocks verified: PASS.

Evidence: `19_STAGE_7_CONTROLLED_MOTION_VERIFICATION.md`.

## Stage 8 — Scientific acquisition
**COMPLETE — 2026-09-12**

- raw XYZ/probe acquisition: PASS;
- microsecond timestamps & monotonic intervals: PASS;
- explicit physical units (mm): PASS;
- metadata & calibration IDs: PASS;
- raw/processed separation (`data/raw/` vs `data/processed/`): PASS;
- uncertainty records: PASS.

Evidence: `20_STAGE_8_SCIENTIFIC_ACQUISITION_VERIFICATION.md`.

## Stage 9 — Scientific surface analysis
**COMPLETE — 2026-09-12**

- plane leveling: PASS (1st-order least squares, tilt residual < 1e-12 mm);
- filtering: PASS (median despiking and Gaussian filtering);
- line profiles: PASS (bilinear interpolation with step-height analysis);
- 2D/3D topography: PASS (publication-grade false-color map and 3D surface mesh);
- roughness metrics: PASS (ISO 25178 Sa, Sq, Sz, Sp, Sv, Ssk, Sku);
- feature dimensions & step heights: PASS;
- particle/object analysis: PASS (8-connected component segmentation, area, volume).

Evidence: `21_STAGE_9_SURFACE_ANALYSIS_VERIFICATION.md`.

## Stage 10 — ML measurement layer
**CURRENT STAGE — PENDING**

- measurement-quality scoring;
- noise/artifact detection;
- anomaly detection;
- feature recognition;
- defect detection;
- ROI detection.

## Stage 11 — Adaptive scanning
**PENDING**

coarse scan
→ ML/scientific quality map
→ feature detection
→ ROI recommendation
→ deterministic safety validation
→ operator approval
→ high-resolution refinement scan

## Stage 12 — Production scientific instrument
**PENDING**

- services;
- structured logs;
- database;
- provenance;
- dashboard;
- GPU analysis;
- reports;
- backups;
- scientific validation.
