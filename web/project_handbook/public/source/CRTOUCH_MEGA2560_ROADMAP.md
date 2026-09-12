# CR Touch and Mega 2560 Roadmap

Status: active implementation roadmap  
Motion policy: xBuddy-only; Mega controls probe I/O, never printer motors

## Phase M0 — Architecture lock

- [x] Select Arduino Mega 2560 Rev3 over Uno R3.
- [x] Assign D8 for protected probe control.
- [x] Assign D3/INT1 for protected trigger input.
- [x] Route both CR Touch grounds through adapter common ground.
- [x] Route probe power through a dedicated protected Mega 5 V branch.
- [x] Select Seeed Base Shield V2 D2 and D8 Grove sockets.
- [x] Allocate D2 socket as Grove Black to Red/GND, Grove Red to Black/VCC,
  and Grove White to Blue/D3.
- [x] Allocate D8 socket as Grove Black to White/GND and Grove Yellow to Yellow/D8.
- [x] Retire J14 as the active CR Touch design.

Exit evidence: maintained architecture and pin-allocation documents agree.

## Phase M1 — Parts and adapter design

- [x] Obtain genuine Mega 2560 Rev3 or electrically equivalent verified board.
- [ ] Obtain keyed CR Touch mating connector and spare harness.
- [x] Obtain two Grove pigtails or keyed Grove plugs for D2 and D8.
- [ ] Measure actual CR Touch current during boot, deploy, stow and idle.
- [ ] Select the probe-branch fuse from measured current and fault margin.
- [ ] Select reverse-polarity, transient and input/output protection.
- [ ] Produce adapter schematic, connector pin numbers and PCB/perfboard layout.
- [ ] Peer-review schematic before assembly.

Exit evidence: signed schematic and bill of materials; no loose-wire prototype.

## Phase M2 — Passive wiring verification

- [ ] Keep the CR Touch disconnected.
- [ ] Verify every harness conductor by continuity, not color.
- [ ] Verify adapter ground topology.
- [x] Set the Base Shield switch to 5V and record the switch position.
- [ ] Verify D2 socket labels by continuity: GND, VCC, D2 and D3.
- [ ] Verify D8 socket labels by continuity: GND, VCC, D8 and D9.
- [ ] Verify no shorts between 5 V, ground, D8 and D3.
- [ ] Verify D8 is inactive at reset and during firmware upload.
- [ ] Verify the D3 test point remains within the Mega input range.

Exit evidence: completed resistance/continuity table with meter and date.

## Phase M3 — Locked firmware

- [x] Compile the locked Mega firmware for `arduino:avr:mega`.
- [x] Confirm the genuine Mega enumerates as `VID 2341 / PID 0042` on COM8.
- [x] Flash the locked Mega firmware with CR Touch disconnected.
- [x] Confirm exact identity response: `SPM_PROBE_MEGA2560`.
- [x] Implement `INFO`, `STATUS`, `READ_TRIGGER` and `SELFTEST`.
- [ ] Keep deploy, stow and arm commands rejected.
- [ ] Add heartbeat timeout and startup safe state.
- [ ] Add deterministic serial framing and command checksums or sequence IDs.

Exit evidence: software tests and a serial transcript with CR Touch disconnected.

## Phase M4 — Controlled probe power

- [ ] Connect only Black, Red and White.
- [ ] Apply power with current monitoring.
- [ ] Record startup, idle and fault current.
- [ ] Stop immediately on heat, smell, alarm or unexpected current.
- [x] Confirm stable 5 V at the Base Shield probe supply.

Exit evidence: voltage/current table and photographs of the adapter.

## Phase M5 — Signal commissioning

- [x] Connect Yellow to the D8 commissioning path.
- [x] Determine deploy/stow timing from verified documentation and measurement.
- [x] Test actuation with the probe mechanically clear of the printer.
- [ ] Measure Blue relative to Red in released and triggered states.
- [x] Connect Blue to the D3 commissioning input path.
- [ ] Record at least 100 manual trigger cycles with no missed or false events.

Exit evidence: timing capture, voltage record and repeatability log.

## Phase M6 — Operator software integration

- [x] Add Mega identity-based port discovery; never bind by COM number alone.
- [x] Add read-only connection and status display.
- [x] Show firmware identity, heartbeat, probe state and fault state.
- [x] Keep simulation state independent from physical connection state.
- [x] Add operator-facing diagnosis for missing/wrong firmware and trigger faults.
- [ ] Require the full commissioning record before allowing probe actuation.

Exit evidence: automated tests plus packaged-software connection check.

## Phase M7 — Supervised system integration

- [x] Mount probe rigidly beside the nozzle.
- [x] Record the mounted reference at nozzle X125/Y105.
- [x] Verify safe retract to Z120 without relying on probe feedback.
- [x] Run stationary trigger tests before any approach.
- [x] Run bounded, watched approach at minimum practical speed.
- [x] Capture electrical trigger at Z16.90 and verify automatic retract.
- [x] Record approximately 2 mm pin travel between physical contact and trigger.
- [x] Keep xBuddy as the sole motion authority.

Exit evidence: supervised test record and explicit Real Measurement approval.

## Phase M8 — Fine profiling subsystem

- [x] Reclassify CR Touch as coarse approach and safety only.
- [x] Lock profiling when no continuous fine sensor is commissioned.
- [x] Lock profiling when no calibrated fine-Z actuator is commissioned.
- [ ] Select the fine profiling sensor.
- [ ] Select the fine-Z/piezo actuator and driver.
- [ ] Verify continuous feedback, calibration, noise and drift.
- [ ] Verify the closed loop in simulation and then with supervised hardware.
- [ ] Hand off at Z19.90, before CR Touch physical contact near Z18.90.
- [ ] Complete at least 10 CR Touch coarse-repeatability cycles and record
  mean, range and standard deviation.

## Phase M9 — Future instrument expansion

- [ ] Environmental temperature/humidity sensor on reserved bus.
- [ ] Independent interlock on D3.
- [ ] Analog force or vibration channel on reserved analog inputs.
- [ ] Isolated auxiliary instrument using a reserved hardware UART.
- [ ] Timestamped event logging and calibration storage.

Each expansion requires its own electrical review and must not weaken the probe
watchdog, safe startup or xBuddy motion boundary.
