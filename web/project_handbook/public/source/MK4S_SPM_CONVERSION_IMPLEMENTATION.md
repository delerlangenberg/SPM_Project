# MK4S SPM Conversion — Supported Implementation

## Purpose

This document is the source of truth for converting the MK4S motion platform
into an SPM prototype using the Arduino Mega 2560 and CR Touch. It distinguishes
implemented software from commissioned hardware and rejects shortcuts that are
not supported by the stock xBuddy firmware.

> **29 July 2026 update:** The commissioned controller is now the Arduino Mega
> 2560, the right-side CR Touch feedback loop has completed a two-object
> full-envelope scan, and SPM Operator v1.2.0.0 includes the verified repeat
> workflow. The earlier E84 phases below are retained as design history. The
> planned nozzle-removed configuration is specified separately in
> [Centered CR Touch Conversion](CENTERED_CRTOUCH_CONVERSION.md).

## Supported architecture

```text
CR Touch coarse safety <-- Mega 2560 <-- USB -----+
Fine profiling sensor <---- instrument interface  +--> PC supervisor
Fine Z/piezo actuator <----- commissioned driver -+
                                                   |
MK4S motors <------------- xBuddy <---- MK4S USB --+
```

- xBuddy owns all X/Y/Z motor movement and printer safety.
- The Mega owns CR Touch actuation, protected trigger input, timestamps and
  its local watchdog.
- The future PC integration identifies the Mega by a firmware identity
  handshake rather than a changing COM number.
- No Mega GPIO is connected to xBuddy STEP, DIR or ENABLE signals.
- No J29 signal injection is used in the stock-firmware implementation.

The mounted 2026-07-28 test measured physical CR Touch contact near Z18.90 and
electrical trigger at Z16.90. The approximately 2 mm pin travel is too large
for CR Touch to serve as the sensitive profiling detector. It remains the
coarse approach and abnormal-contact safety channel. Normal profiling hands off
to a separate fine sensor and fine-Z actuator near Z19.90.

## Why the proposed J29 workflow is rejected

The Prusa accessory documentation describes J29 pin 1 / PA10 as the SPI2 chip
select and an **open-drain output**, limited to 3.3 V and 5 mA. It is not a
documented external Z-probe input. Treating it as a push-pull trigger input can
create contention when xBuddy drives the line.

The current Prusa Buddy firmware implementation of `G30` accepts X, Y and E
parameters. It does not implement the proposed `G30 P10 S1` custom-pin probe.
The proposed `M226 P10 S1` and `M43 P10 S0` sequence is likewise not an
established stock MK4S interface. Marlin documentation for other controllers
does not prove those commands are enabled or safe on Prusa Buddy firmware.

Using J29 for direct trigger integration would therefore be a separate custom
xBuddy firmware and electrical-engineering project. It would require pin
ownership changes, input protection, boot-state analysis, motion-stop timing,
fault handling, firmware signing/flashing decisions and regression testing.

## Acquisition modes

| Mode | Hardware | Status |
|---|---|---|
| Simulation | None | Available |
| Dry Run | None; complete virtual workflow | Available |
| Real Measurement | MK4S + commissioned Mega 2560 + commissioned CR Touch | Available only through the commissioned right-side profile and live readiness gates |

USB presence alone never unlocks real measurement. The current Mega readiness
gate requires:

1. exactly one `VID_2C99&PID_001A` MK4S;
2. exactly one Mega controller returning identity `SPM_PROBE_MEGA2560`;
3. successful Mega `INFO`, `STATUS` and heartbeat exchange;
4. protocol version 1;
5. a completed Mega/adapter hardware verification record;
6. a non-empty calibration revision;
7. healthy status, diagnostics and heartbeat;
8. an explicit operator hardware authorization.

Run the read-only gate report:

```powershell
.\.venv\Scripts\python.exe tools\spm_system_readiness.py --mode real_measurement
```

Simulation and Dry Run can be checked with `--mode simulation` and
`--mode dry_run`; they remain available when hardware is absent or locked.

## Implementation phases

### Phase A — host and firmware foundation (implemented)

- exact dual-USB discovery;
- typed E84 identity, status and diagnostic parsing;
- non-actuating heartbeat command;
- explicit real-measurement blockers;
- factory-OOB firmware detection;
- software-only Simulation and Dry Run;
- xBuddy `M119` prohibited as CR Touch feedback.

### Phase B — flash locked E84 firmware

Install the complete ModusToolbox build tools, build the existing multi-core
application and flash it through J1 with the CR Touch disconnected. The first
flash must leave `SPM_EDGE_HARDWARE_VERIFIED=0`, all probe outputs inactive and
`GET_DIAGNOSTICS` reporting probe channels as `NOT_TESTED`/`LOCKED`.

### Phase C — passive electrical commissioning

Build the protected adapter and complete every measurement in
`firmware/crtouch_edge_controller/docs/COMMISSIONING.md`. Verify the actual
harness conductors, supply current, common ground, 0–3.3 V conditioned input,
buffered control output and safe boot/reset states. Do not rely on wire colour.

### Phase D — controlled probe commissioning

Enter measured polarity and timing, enable the hardware flag, use peripheral
PWM rather than one-shot GPIO delays, and verify deploy/stow/trigger/release.
Complete at least 100 repeatability cycles with watchdog and timeout tests.

### Phase E — dual-USB approach coordinator

The coordinator may issue only bounded, slow xBuddy moves. It checks E84 state
between steps, stops new downward commands immediately on trigger or transport
loss, sends the authorized xBuddy retract sequence and verifies the resulting
position. This is supervisory PC control, not a deterministic hard-real-time
motor interlock.

### Phase F — mechanical conversion

Do not remove the LoveBoard, loadcell or complete extruder assembly during the
software/electrical validation phases. Mechanical conversion requires a
separate reviewed plan covering xBuddy firmware expectations, missing heater/
thermistor/fan peripherals, homing behavior, moving mass, cable strain relief,
probe bracket rigidity, travel limits and a reversible recovery configuration.

## Definition of ready

“System ready” means every software gate and physical commissioning record has
passed. It does not mean that a UART message was printed, an output command was
sent, or a disconnected input happened to read high or low.
