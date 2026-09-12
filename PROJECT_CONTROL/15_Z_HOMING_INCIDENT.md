# Z Homing Incident — Investigation Open

Operator reported unsafe downward Z motion during calibration on 2026-09-12.

## Confirmed code findings

- Calibration bypassed the central supervisor and issued G28.
- Direct Z approach contains no Arduino feedback read.
- Z stop sets a software event checked between commands.
- The response reader extends its deadline on echo:busy.
- The calibration summary contradicts its individual endstop fields.
- Only the calibration timestamp changed relative to the committed record.

## Containment

Calibration entry points blocked.
Direct Z serial entry points blocked for execution; previews retained
where the function provides an execute flag.
Compact control stop label corrected to describe a software request.

## Remaining work

Inventory other direct motion routes and firmware behavior.
Design one enforced physical-command authority.
Verify feedback freshness, contact detection, bounded travel,
timeout behavior, and actual stop latency before hardware testing.
Calibration remains untrusted. No physical operation is authorized.


## Mandatory Arduino-loss behavior

User requirement: Z must stop if Arduino stops responding.

- No physical Z command without fresh, valid feedback.
- Missing, stale, malformed, or disconnected feedback latches a fault.
- Fault handling must stop executing motion and cancel queued motion.
- No automatic retract or automatic restart after feedback loss.
- Communication recovery alone must not clear the fault.
- Operator acknowledgement and a new preflight are required.
- Feedback deadline and maximum stopping distance must be derived
  and verified before commissioning; no arbitrary production values.
- A software event or stopped command stream is not proof of physical stop.
- Existing calibration and direct Z execution blocks remain in place.

Status: requirement recorded; physical stop implementation unverified.
