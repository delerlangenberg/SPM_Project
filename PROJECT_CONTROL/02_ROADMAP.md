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
**CURRENT STAGE — IN PROGRESS**

- create reproducible dependency file: COMPLETE (`pyproject.toml`);
- restrict pytest discovery to `tests/`: COMPLETE;
- remove obsolete migration clutter: PENDING REVIEW;
- commit clean baseline: PENDING;
- create one labeled stage recovery backup: PENDING;
- update documentation: IN PROGRESS.

## Stage 4 — USB migration to Spark
**PENDING**

Only after Stage 3.

- connect MK4S USB-C;
- connect Arduino USB;
- enumerate with Linux only;
- identify VID/PID/serial;
- create stable udev aliases;
- verify permissions;
- no motion.

## Stage 5 — Read-only hardware communication
**PENDING**

- identity;
- firmware;
- temperature;
- endstop/probe state;
- XYZ position;
- Arduino identity/status;
- disconnect/reconnect;
- timeout handling.

No motion.

## Stage 6 — Deterministic hardware safety gate
**PENDING**

Define:

- coordinate limits;
- safe Z;
- calibration validity;
- probe state;
- fault handling;
- abort;
- interlocks;
- operator authorization;
- command policy.

## Stage 7 — Controlled motion commissioning
**PENDING**

Introduce minimal-risk movement only after deterministic safety gate passes.

## Stage 8 — Scientific acquisition
**PENDING**

- raw XYZ/probe acquisition;
- timestamps;
- units;
- metadata;
- calibration IDs;
- raw/processed separation;
- uncertainty records.

## Stage 9 — Scientific surface analysis
**PENDING**

- plane leveling;
- filtering;
- line profiles;
- 2D/3D topography;
- roughness metrics;
- feature dimensions;
- particle/object analysis.

## Stage 10 — ML measurement layer
**PENDING**

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
