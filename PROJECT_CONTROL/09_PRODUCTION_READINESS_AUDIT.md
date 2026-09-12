# Production Readiness Audit

**Audited:** 2026-09-11

## Decision

This repository is a promising educational and simulation prototype. It is not
ready to be represented as a scientific measurement instrument, and real scan
or contact-profiling features must remain disabled. The primary blockers are
unverified sensing, non-centralized motion authorization, missing measurement
provenance, and inadequate behavioural verification.

The target should be a traceable research instrument platform first. Claims
comparable to Bruker or Oxford Instruments require a separately planned quality
system, verification/validation programme, service process, calibrated hardware,
and regulatory assessment where applicable.

## Findings

### P0 - Do not enable real measurement

1. `core/web/real_scan_control.py` treats `M114` printer-coordinate readback as
   the real constant-Z measurement. It calculates `surface_height` from that
   coordinate minus the command setpoint. This is not a calibrated surface
   sensor and cannot establish topography, feedback error, force, or uncertainty.

2. The foil-tap path performs repeated physical contact based on experimental
   `M119 z_min` status. The project architecture correctly states that CR Touch
   is a coarse safety probe rather than a continuous fine-profile sensor, but
   the real scan runner can still enable contact mapping with environment flags.

3. Direct serial scan code has its own environment-variable gates and serial
   protocol. It does not call one authoritative interlock/state-machine service
   for every command. An environment variable is useful for development but is
   not an operator authorization, hardware interlock, watchdog, or emergency
   safety channel.

4. Stop/pause is cooperative between commands. There is no verified bounded
   stop latency, independent emergency stop circuit, command watchdog, or
   deterministic recovery/retract procedure after USB, firmware, sensor, or
   process failure.

### P1 - Measurement integrity and deployment

1. Acquired frames are CSV-oriented point arrays without an immutable run
   manifest. A professional run must bind raw samples to instrument identity,
   firmware, probe and actuator serials, calibration versions, units, scan plan,
   timestamps/timebase, operator, environmental conditions, events, processing
   history, software build, and content hashes.

2. Calibration data records printer counts and position but lacks traceable
   standards, calibration procedure/version, uncertainty budget, acceptance
   criteria, expiry, environmental conditions, signed approval, and a direct
   link to each dataset.

3. The deployed Linux target retains Windows `COM6` configuration. The web
   control function only accepts `COM1` to `COM10`, so configured Linux device
   paths such as `/dev/ttyACM0` cannot be selected through that route.

4. Local-only deployment must retain secret-scanning and ignore rules. The
  runtime must not require or accept cloud-provider credentials.

### P1 - Engineering and verification

1. The canonical suite reported `25 passed, 1 failed`: it requires a missing
   `docs/webui_backup_*.zip`. The repository has no visible dependency manifest
   or pytest configuration, so a clean, repeatable install and test command is
   not defined.

2. Most operator-workstation tests assert source strings rather than executing
   the UI, safety gate, serial transport, or scan logic. They detect text drift,
   not a reliable instrument behaviour.

3. `core/web/system_control.py` contains earlier function definitions followed
   by a later “override” implementation in the same module. Python silently
   replaces the earlier definitions. This makes the active safety contract hard
   to review and creates a serious regression risk.

4. The legacy `core/scan/workflow/spm_workflow.py` imports `control`,
   `analysis`, and `processing` modules outside the present package structure.
   It is not a viable controlled workflow until it is either repaired and
   tested or retired.

## Target Architecture

```
Operator client / API
        |
Experiment service -> immutable run store -> deterministic processing -> reports
        |
Safety supervisor (single command authority, audited state machine)
        |
Hardware adapter layer -> independent interlock / E-stop / watchdog
        |
Calibrated XY stage + fine Z actuator + continuous sensor + environment sensors
```

The safety supervisor owns explicit states such as `DISCONNECTED`, `READ_ONLY`,
`COMMISSIONING`, `READY`, `ARMED`, `APPROACHING`, `ACQUIRING`, `RETRACTING`,
`FAULT`, and `E_STOP`. Every state transition must have typed guards, event
records, timeouts, and a tested fail-safe action. LLMs can read a redacted run
summary and return typed recommendations, but can never issue a command or
change a guard.

## Delivery Plan

### Phase A - Stabilize the baseline

- Keep USB disconnected and all real-motion flags disabled.
- Remove cloud-provider integrations and add a secret-scanning and ignore policy.
- Add `pyproject.toml` or equivalent locked dependency manifest, supported
  Python versions, pytest configuration, and a single CI command.
- Replace the missing archival-zip assertion with an explicit release artifact
  contract, or add the approved artifact to the release process.
- Split duplicated web-control implementations and make the Linux device model
  explicit using stable `/dev/serial/by-id` identities.

### Phase B - Build the safety kernel

- Define the finite state machine and typed command/event contracts.
- Route *all* serial I/O through one transport owned by the safety supervisor.
- Add hardware-independent simulation/fault injection for timeout, stale
  readback, disconnect, invalid sensor data, over-limit, and emergency stop.
- Add command acknowledgement, position tolerance, watchdog, audit log, and
  verified recovery behaviour before any hardware commissioning.

### Phase C - Commission a measurement chain

- Select and integrate a continuous, calibrated fine sensor and fine Z actuator.
- Establish traceable XY/Z/lateral-scale, height, noise, drift, hysteresis,
  repeatability, linearity, bandwidth, and environmental calibration methods.
- Define acceptance criteria and uncertainty budgets for each supported mode.
- Gate `ARMED` and `ACQUIRING` on current calibration and successful preflight.

### Phase D - Scientific data and analysis

- Persist raw data in a versioned, self-describing format such as HDF5/OME-NGFF
  or Zarr, with a JSON run manifest and append-only event log.
- Preserve immutable raw samples. Model each processing operation as a versioned
  recipe with parameters, software build hash, input/output hashes, and units.
- Implement reproducible flattening, line correction, filtering, segmentation,
  roughness/PSD/feature analysis, uncertainty propagation, and report export.
- Verify algorithms against synthetic truth and reference datasets; publish
  tolerances and test fixtures.

### Phase E - LLM-assisted operation and analysis

- Use retrieval over approved SOPs, calibration records, and run metadata.
- Require structured, schema-validated advice with evidence references and
  confidence/abstention; retain prompt, model, context versions, and response.
- Limit the LLM to explanation, anomaly triage, analysis recipe proposals, and
  report drafting. A deterministic validator and human approval own every
  proposed plan.
- Evaluate with a held-out instrument dataset, adversarial prompts, unsafe-plan
  rejection tests, and operator usability studies before release.

## Exit Criteria for a Research Release

- All P0 findings resolved and independently tested in simulation and on a
  controlled commissioning fixture.
- Fresh calibration, traceable acceptance evidence, and an uncertainty statement
  are attached to every supported measurement mode.
- CI is green from a clean environment, including unit, integration, fault,
  and end-to-end simulated-run tests.
- A complete run can be replayed to reproduce its derived analysis and report.
- Real-hardware commissioning is separately approved with documented residual
  risk. No claim of commercial-instrument equivalence is made without a formal
  quality and validation programme.