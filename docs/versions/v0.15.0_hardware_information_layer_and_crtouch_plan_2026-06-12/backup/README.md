# Educational SPM v0.15.0 - Hardware Information Layer and CR-Touch Plan

Date: 2026-06-12

## Scope

This checkpoint continues the two-layer development strategy:

1. Hardware Test Layer first.
2. Measurement Layer only after hardware tests are trusted.

It also incorporates the CR-Touch Z scanner PDF and creates a boundary for a future Academic AI API integration.

## Added

- `core/system/hardware_information_exchange.py`
- `core/application/hardware_information_cli.py`
- `tests/test_hardware_information_exchange.py`
- `docs/TWO_LAYER_SPM_DEVELOPMENT_ROADMAP_2026-06-12.md`
- `docs/CRTOUCH_SPM_Z_SCANNER_PHASE_PLAN_2026-06-12.md`
- `docs/ACADEMIC_AI_API_INTEGRATION_PLAN_2026-06-12.md`

## Updated

- `core/z_control/crtouch_probe_plan.py`
- `tests/test_crtouch_probe_plan.py`

## Hardware Information Layer

Read-only actions:

- `IDENTITY -> M115`
- `TEMPERATURE -> M105`
- `ENDSTOPS -> M119`
- `POSITION -> M114`
- `ALL -> all read-only actions`

Default mode is dry-run:

```powershell
.\.venv\Scripts\python.exe -m core.application.hardware_information_cli ALL
```

Real read-only exchange:

```powershell
.\.venv\Scripts\python.exe -m core.application.hardware_information_cli ALL --real
```

Motion commands are rejected from this layer.

## CR-Touch PDF Notes Integrated

The CR-Touch Z scanner plan now records:

- Steel needle is the recommended precision tip.
- Pogo pin is optional and safer but less precise.
- 2 x 2 mm magnet is mandatory for the pogo option.
- PTFE tube: 2 mm OD / 1 mm ID.
- Guide hole: 2.0-2.1 mm.
- Guide length: 10-15 mm.
- Probe axis must be vertical.
- Manual trigger repeatability must be tested before software-controlled approach.

## Academic AI API Boundary

The Academic AI API is planned as analysis/report/documentation support only.

It must not:

- Send G-code.
- Start motion.
- Override limits.
- Decide hardware safety state.

## Verification

- Hardware information CLI dry-run passed.
- Real read-only hardware exchange passed on COM5.
- `M115`: firmware identity confirmed.
- `M105`: temperature/status readback succeeded.
- `M119`: all endstops open.
- `M114`: position readback succeeded at `X=125.00`, `Y=105.00`, `Z=120.00`.
- Full test suite passed: 136 tests.

## Backup

Edited files are backed up in:

`docs/versions/v0.15.0_hardware_information_layer_and_crtouch_plan_2026-06-12/backup/`
