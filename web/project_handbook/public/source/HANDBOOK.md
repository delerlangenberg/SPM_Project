# SPM Prusa Project Handbook

> **Documentation authority:** This handbook and its linked engineering records
> are the project's maintained source of truth. The current project webpage is a
> presentation and demonstration view only. A later operator interface may show
> live measurements, analysis and approved commands, but it must consume
> validated software data and must not replace the handbook or bypass hardware
> safety controls.

## 1. What this project is

The project converts a Prusa MK4S motion platform into a controlled scanning
and single-point measurement research prototype. The xBuddy remains responsible
for safe X/Y/Z motion. An Arduino Mega 2560 Rev3 supervises the protected
CR Touch interface and future instrument I/O. The Windows SPM Operator
application coordinates both devices over separate USB connections.

```text
CR Touch ↔ protected adapter ↔ Mega 2560 ↔ USB ↔ SPM Operator
                                                     ↕
                                            USB ↔ MK4S xBuddy
```

The current supported architecture does not connect Mega GPIO to xBuddy
STEP/DIR/ENABLE or inject a trigger into J29.

### Authoritative operator coordinate convention

All operator commands, plots, CSV exports, and spoken directions describe the
**CR Touch measurement point moving across the sample**. They do not describe
which printer mechanism happens to move.

The viewpoint is always the operator standing in front of the Prusa:

```text
                    BACK (-Y)
                       ↑
                       |
       LEFT (-X) ← CR TOUCH → RIGHT (+X)
                       |
                       ↓
                    FRONT (+Y)
                       USER
```

| Operator command | Measurement meaning | Internal machine action |
|---|---|---|
| CR Touch +X / right | Measurement point moves right | X mechanism moves right |
| CR Touch -X / left | Measurement point moves left | X mechanism moves left |
| CR Touch +Y / front | Measurement point moves toward operator | Stage moves backward |
| CR Touch -Y / back | Measurement point moves away from operator | Stage moves forward |
| CR Touch +Z / up | Probe/nozzle moves away from sample | Z mechanism moves up |
| CR Touch -Z / down | Probe/nozzle moves toward sample | Z mechanism moves down |
| Probe Out | Pin extends from housing | Firmware deploy action |
| Probe In | Pin retracts into housing | Firmware stow action |

Operator-facing software must show the measurement target first. When useful,
it may show a second line such as `Machine action: stage moves backward`.
Raw stage direction must never replace the CR Touch measurement direction.

CR Touch is the validated **coarse-approach and safety channel**, not the
continuous SPM profiling sensor. Mounted testing measured first physical
contact near Z18.90 and electrical trigger at Z16.90, approximately 2 mm later.
Normal profiling must hand off near Z19.90 to a separate calibrated fine sensor
and fine-Z actuator.

The complete validated tapping, profiling, speed, adaptive-map, AI, and
purchasing record is maintained in
[CR Touch Tapping Development Record](CRTOUCH_TAPPING_DEVELOPMENT_RECORD.md).

### Current Stage 2 conversion status

On 30 July 2026 the nozzle, heater, hotend thermistor and toolhead fans were
removed and the CR Touch was mounted near the former nozzle centerline. The
centered profile completed monitored commissioning:

| Stage 2 item | Current state |
|---|---|
| Mechanical conversion | Installed and operator verified |
| xBuddy communication | Stock 6.2.4+8909; bounded XYZ and precise XY homing passed |
| Heater targets/outputs | Verified zero |
| Mega control | D8 high impedance |
| Probe trigger | D3 LOW/unlatched in final safe state |
| New XY envelope | X15.50–250.00, Y12.50–210.00 mm |
| Safe XY/retract | Z45.00 mm |
| Mean bare-stage trigger | Z28.11 mm |
| Five-point stage variation | 0.60 mm peak-to-peak |
| Real Measurement | Available only through all live safety gates |

The 29 July right-side envelope remains historical evidence only and must not
be used for Stage 2 motion. The machine-readable profile and lockout files are
authoritative.

## 2. Where to begin

### I want to operate or test the software

1. Read the [Software User Guide](SPM_OPERATOR_SOFTWARE_USER_GUIDE.md).
2. Check [Software Readiness](SOFTWARE_READINESS_2026-07-20.md).
3. Use **Simulation** or **Dry Run** until Real Measurement is explicitly
   unlocked.
4. Install with
   [`installer/windows/SPM_Operator_Setup.exe`](../installer/windows/SPM_Operator_Setup.exe).

### I want to work on CR Touch

1. Read the [CR Touch subject guide](subjects/CRTOUCH.md).
2. Follow the canonical
   [Mega 2560 integration](CRTOUCH_MEGA2560_INTEGRATION.md).
3. Complete the
   [Mega 2560 roadmap](CRTOUCH_MEGA2560_ROADMAP.md) in order.
4. Do not solder or enable outputs until the adapter schematic, harness
   continuity and passive measurements are recorded.

### I want to work on the PSoC Edge E84

1. Read the [PSoC subject guide](subjects/PSOC_EDGE_E84.md).
2. Review the [integration architecture](PSOC_EDGE_E84_INTEGRATION_ARCHITECTURE.md).
3. Treat the former J14 CR Touch firmware as retained research history.
4. Do not connect CR Touch to USB-C wiring or unpopulated J14 pads.

### I want to work on MK4S motion

1. Read the [MK4S subject guide](subjects/MK4S.md).
2. Review the [bring-up checklist](MK4S_BRINGUP_CHECKLIST.md).
3. Use the documented USB/G-code interface. Do not solder to internal driver
   nets or repurpose J29 without a separate reviewed custom-firmware project.

## 3. Operating modes

| Mode | Physical motion | Probe source | Current availability |
|---|---:|---|---|
| Simulation | No | Generated | Ready |
| Dry Run | No | Generated through full workflow | Ready |
| Real Measurement | Yes | Commissioned Mega 2560/CR Touch | Ready with OPERATIONAL authorization, healthy COM6/COM8, D3 LOW/unlatched, zero thermal outputs and the centered profile |

### Adaptive object-map resolution

SPM Operator v1.3.0.0 provides three explicit physical refinement modes:

| Mode | Discovery pitch | Focused pitch | Intended use |
|---|---:|---:|---|
| Quick | 20 mm | 5 mm | Fast location and coarse footprint |
| High | 20 mm | 2.5 mm | Recommended repeatable object map |
| Research | 15 mm | 1 mm | Slow exploratory run with active temperature monitoring |

Pitch is XY sample spacing, not claimed instrument resolution. CR Touch
overtravel and trigger repeatability remain the limiting factors.

## 4. Source-of-truth documents

- [Supported conversion implementation](MK4S_SPM_CONVERSION_IMPLEMENTATION.md)
- [Centered CR Touch conversion plan](CENTERED_CRTOUCH_CONVERSION.md)
- [Stage 2 LoveBoard connector assessment](STAGE2_LOVEBOARD_CONNECTOR_ASSESSMENT.md)
- [PSoC integration architecture](PSOC_EDGE_E84_INTEGRATION_ARCHITECTURE.md)
- [Operator software user guide](SPM_OPERATOR_SOFTWARE_USER_GUIDE.md)
- [Professional roadmap](SPM_PROFESSIONAL_PHASE_ROADMAP.md)
- [CR Touch Mega 2560 integration](CRTOUCH_MEGA2560_INTEGRATION.md)
- [CR Touch Mega 2560 roadmap](CRTOUCH_MEGA2560_ROADMAP.md)
- [CR Touch tapping development and purchasing record](CRTOUCH_TAPPING_DEVELOPMENT_RECORD.md)
- [Tapping mode, AI and piezo roadmap](TAPPING_MODE_AI_PIEZO_ROADMAP.md)
- [Stage 2 release record](RELEASE_v1.3.0.0.md)
- [Project documentation map](README.md)

## 5. Project directory map

| Path | Meaning |
|---|---|
| `core/` | Active Python application and hardware abstractions |
| `firmware/crtouch_mega2560_controller/` | Active locked CR Touch controller firmware |
| `firmware/crtouch_edge_controller/` | Superseded E84/J14 research implementation |
| `web/operator_console/` | Existing operator web console |
| `web/project_handbook/` | Presentation/demo view of selected handbook content; not the authoritative engineering record |
| `docs/` | Maintained handbook, subject guides, reports and evidence |
| `Hardware/` | Mechanical/electrical source material and purchasing |
| `tests/` | Active automated regression tests |
| `installer/windows/` | The single canonical Windows installer |
| `backups/phase_milestones/` | The one retained recovery archive |
| `packaging/` | Reproducible packaging definitions |

## 6. Documentation rules

1. Update the subject guide when adding a new document.
2. Mark measurements as verified, provisional or untested.
3. Never call a sent command a verified electrical result.
4. Keep historical phase notes for evidence only; current architecture
   documents take precedence.
5. Place installers only in `installer/windows`.
6. Keep generated `build/`, `dist/`, caches and temporary clones out of the
   maintained project.

## 7. Stage 2 completion record

Stage 2 centered-probe commissioning is complete. The software release is
v1.3.0.0, the Python suite passed 356 tests, and both portable and installed
applications were launch-tested outside the source tree. The recovery copy is
`D:\SPM_Prusa_Project\backups\phase_milestones\v1.3.0.0_stage2_centered_verified_20260730`.

The machine was left at X132.75, Y111.25, Z45.00 with **Probe In**, D3 LOW and
unlatched, and D8 high-impedance. This is the recorded state from commissioning,
not a substitute for the live safety checks performed before each Real
Measurement.
