# Centered CR Touch / Nozzle-Removed Conversion

## Status

**Software profile:** commissioned in v1.3.0.0  
**Mechanical conversion:** installed and operator verified 30 July 2026  
**Real motion:** available through live Stage 2 safety gates  
**Custom MK4S firmware flashing:** unnecessary and not performed

### Current read-only evidence

With no movement or probe actuation, the installed stock controller reported:

| Check | Evidence |
|---|---|
| xBuddy firmware | Prusa-Firmware-Buddy 6.2.4+8909 |
| Final safe position | X132.75, Y111.25, Z45.00 |
| Removed hotend input | T -20.00 °C, target 0, heater output 0 |
| Bed | 25.95 °C, target 0, output 0 |
| Endstops | all open |
| Mega firmware | 0.8.5-lcd-rgb-approach |
| Probe control | D8 high impedance |
| Probe trigger | D3 LOW and unlatched |

The stock xBuddy completed bounded Z motion, X/Y precise homing, the complete
verified envelope and five-point stage probing without requiring a custom
firmware flash.

### Commissioned geometry

| Item | Verified value |
|---|---:|
| X envelope | 15.50–250.00 mm |
| Y envelope | 12.50–210.00 mm |
| Usable field | 234.50 × 197.50 mm |
| Safe XY/retract | Z45.00 mm |
| Upper Z reference | Z220.00 mm |
| Mean bare-stage trigger | Z28.11 mm |
| Bare-stage range | Z27.80–28.40 mm |

## Goal

Place the CR Touch sensing axis on the former nozzle centerline. This removes
the approximately 51 mm lateral probe offset and should recover more symmetric
XY reach. The conversion does not improve CR Touch trigger physics; it improves
geometry and reduces coordinate-offset risk.

## Why removing the nozzle affects the MK4S

The MK4/MK4S uses its nozzle/loadcell system for Z homing, mesh probing and
loadcell tests. Prusa's assembly documentation explicitly uses the nozzle
during loadcell calibration. Removing or mechanically replacing that assembly
can therefore invalidate stock homing assumptions.

The xBuddy also monitors hotend heater, thermistor, fans and toolhead wiring.
Deleting those parts or bypassing their faults is not a harmless software
setting. A thermal safety input must never be replaced with a fixed resistor
merely to hide an alarm.

Official engineering references:

- [Prusa Firmware Buddy source](https://github.com/prusa3d/Prusa-Firmware-Buddy)
- [MK4S assembly and loadcell test guide](https://help.prusa3d.com/wp-content/uploads/generated/original-prusa-mk4s-kit-assembly_2167_guide_707794_en_2026-05-06.pdf)

Prusa documents that custom Buddy firmware requires the custom-firmware
flashing procedure, including an irreversible board appendix change. That is
not authorized during this design phase.

## Recommended mechanical architecture

The first centered prototype should be reversible:

1. Remove filament and cool the toolhead fully.
2. Preserve the complete stock hotend, nozzle, heater and thermistor as a
   labelled recoverable assembly.
3. Design a rigid adapter that places the CR Touch pin axis on the nozzle
   centerline without loading the CR Touch housing.
4. Keep the LoveBoard, cable strain relief and required toolhead electronics.
5. Do not use the CR Touch body as an endstop or structural member.
6. Measure pin-to-carriage and pin-to-bed clearances throughout full travel.

Whether the stock loadcell can remain mechanically present with a center probe
must be decided from the mount design. If it cannot remain functional, stock
automatic Z homing is unavailable and the software must use a separately
commissioned CR Touch reference routine.

## Software behavior in centered mode

The profile `center_crtouch_nozzle_removed` is present in
`config/crtouch_mount_profiles.json` but disabled. When selected before
commissioning, SPM Operator must fail closed.

Centered mode requires:

- all extrusion commands rejected;
- all nozzle-heating commands rejected unless the retained thermal assembly is
  separately approved;
- no print job or filament workflow;
- no stock Z home assumed;
- a new X/Y envelope measured from scratch;
- a new bare-stage CR Touch Z reference;
- Probe In before XY travel unless the validated scan routine explicitly
  requires Probe Out;
- five-cycle actuation/trigger test and monitored corner checks;
- signed operator commissioning record.

## Firmware strategy

### Stage 1 — stock firmware plus scanner command firewall

Preferred for the first mechanical prototype. Keep xBuddy responsible for X/Y/Z
motion, but use only an approved scanner command subset:

```text
Allowed: M115 M105 M119 M114 M17 M18 M400 G90 G91 bounded G0/G1
Output-off only: M104 S0, M140 S0, M107
Blocked: nonzero heating, all E-axis moves, print/filament operations,
         G28/G29 and unknown commands
```

The host command firewall is the preferred current solution because it retains
stock motor limits, watchdogs and recovery firmware while making the removed
printing tool inaccessible to the SPM workflow. The application must validate
`M105` before motion and reject the session unless the removed-hotend input is
cold/open and every heater target/output is zero.

### Stage 2 — dedicated Buddy scanner fork, only if stock firmware blocks safe use

Create a fork pinned to the exact official MK4S firmware tag installed on the
machine. The fork should add a clearly visible **SPM Scanner Mode**, not remove
safety checks globally.

Scanner Mode design requirements:

- power-on default is disabled;
- extrusion and heating command paths return explicit errors;
- print/filament UI is hidden or disabled only in scanner builds;
- X/Y/Z limits and motor-current protections remain;
- missing peripherals are handled through explicit build-time scanner
  configuration, not random alarm suppression;
- a dedicated homing state machine uses the external commissioned probe;
- watchdog, emergency stop and USB-loss behavior remain fail closed;
- firmware identifies itself as a custom SPM build through `M115`;
- stock firmware recovery image and procedure are prepared before flashing.

### Stage 3 — flash authorization

Flashing remains blocked until:

1. source fork and exact upstream tag are recorded;
2. reproducible firmware build passes;
3. command allowlist/denylist tests pass on a bench controller;
4. electrical review confirms heater/thermistor/loadcell disposition;
5. stock recovery is tested;
6. the operator explicitly authorizes the irreversible custom-firmware step.

## Commissioning sequence

1. Photograph and measure the stock assembly before removal.
2. Back up printer settings and record current `M115`, `M503`, `M211`, `M92`,
   and read-only diagnostic output where supported.
3. Install the reversible centered mount with power disconnected.
4. Verify wiring continuity and toolhead clearances.
5. Power only for read-only checks.
6. Verify Mega identity and Probe In/Out five times.
7. Establish conservative X and Y limits in 5 mm monitored steps.
8. Establish a bare-stage Z reference at an empty safe point.
9. Run four-corner no-object checks.
10. Run a low-resolution known-object scan.
11. Enable High resolution only after the known object is reconstructed.

## Release boundary

SPM Operator v1.3.0.0 contains the commissioned Stage 2 profile, live thermal
and trigger gates, scanner command firewall and adaptive-scan geometry. The
custom Buddy fork remains a research contingency only; stock firmware proved
adequate and retained its motor limits, precise XY homing and watchdogs.

See [LoveBoard Connector Assessment](STAGE2_LOVEBOARD_CONNECTOR_ASSESSMENT.md)
for the decision to retain the Mega as CR Touch controller.
