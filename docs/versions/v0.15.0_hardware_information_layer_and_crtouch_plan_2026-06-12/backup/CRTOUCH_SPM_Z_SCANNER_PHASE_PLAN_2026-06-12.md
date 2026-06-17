# CR-Touch Educational SPM Z Scanner Phase Plan

Date: 2026-06-12

Source document:

`Hardware/CRTouch_SPM_FINAL_Project.pdf`

## Design Summary

The CR-Touch will be treated as a contact-based Z probe for the Educational SPM project. It is not yet the active measurement controller. It must first pass isolated hardware tests before it can be used in the measurement layer.

Working principle:

- CR-Touch has a spring-loaded probe and internal magnet.
- Hall-effect sensing detects magnet displacement.
- The controller outputs a digital trigger.
- Replacing the probe with a needle or pogo pin makes it a macro-scale contact probe.
- An external guide/PTFE tube improves vertical stability and repeatability.

## Probe Options

### Option A - Steel Needle

Recommended for first precision build.

- Approximately 1 mm diameter.
- Cut to approximately 18 mm.
- Higher repeatability.
- Single spring system: CR-Touch spring only.
- Sharper tip gives better spatial resolution.

### Option B - Pogo Pin

Optional safer contact path.

- P50-B1 or P75-B1.
- Built-in spring reduces hard contact risk.
- Requires glued 2 x 2 mm neodymium magnet.
- Creates a double-spring system, so precision is lower.

## Mechanical Requirements

- CR-Touch sensor.
- 2 x 2 mm neodymium magnet.
- PTFE tube: 2 mm OD / 1 mm ID.
- Guide hole: 2.0-2.1 mm.
- Guide length: 10-15 mm.
- Rigid mount.
- Probe axis must be vertical.
- Motion must be smooth with minimal friction.

## Hardware-Layer Test Phases

### Phase Z1 - Documentation and Build Readiness

Status: started.

- Record BOM.
- Record selected probe option.
- Keep CR-Touch real hardware disabled in software.
- Confirm no measurement code depends on CR-Touch until testing is complete.

### Phase Z2 - Manual Mechanical Test

No software motion.

- Install probe tip.
- Verify guide motion by hand.
- Press probe manually.
- Confirm repeatable trigger behavior outside scanning.
- Adjust magnet position if unstable.

### Phase Z3 - Electrical Information Test

No Z motion.

- Confirm wiring and power.
- Confirm digital trigger can be read.
- Log trigger state.
- Identify controller/port if the CR-Touch uses a separate microcontroller.

### Phase Z4 - Slow Z Approach Test

Supervised only.

- Use very slow Z movement.
- Start from safe retract height.
- Stop immediately on trigger.
- Retract to safe height.
- Save trigger Z and raw event log.

### Phase Z5 - Repeatability Test

Supervised only.

- Repeat approach at the same XY point.
- Record trigger Z values.
- Compute spread/repeatability.
- Pass only if trigger is stable enough for educational topography.

## Measurement-Layer Phases

Only after hardware-layer phases pass:

### Phase M1 - Single-Point Contact Height

- Move to one XY point.
- Approach until trigger.
- Record contact Z.
- Retract.

### Phase M2 - X-Line Contact Profile

- Repeat single-point contact over a short X line.
- Save line profile.
- Plot X versus contact Z.

### Phase M3 - Small XY Topography

- Run 2 x 2, then 3 x 3, then 10 x 10.
- Save partial data after every point.
- Always retract and return to safe center.

### Phase M4 - Future Constant-Height / Feedback Mode

- Not active yet.
- Requires a continuous feedback signal, not only digital trigger.
- Academic/analysis tools may help interpret results, but cannot control safety-critical motion.

## Safety Rules

- Needle tips are sharp; handle carefully.
- Use slow Z movement.
- Avoid hard collisions.
- Keep magnets away from sensitive electronics.
- Keep CR-Touch real hardware disabled until wiring, trigger repeatability, and port identity are confirmed.
