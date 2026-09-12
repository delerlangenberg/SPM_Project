# Hardware Safety and USB Gate

Updated: 2026-09-12

## Authorization

**BLOCKED — baseline closeout only.**

Do not open serial sessions, issue G-code, actuate the probe, home,
calibrate, or start physical scans during this stage.
This documentation update does not change runtime interlocks.

## Historical connections

Earlier records report MK4S and Arduino USB connections on Spark.
The previous instruction saying they had not yet connected was stale.
Current connection, position, calibration, and probe state are unverified.
This procedure does not require changing cables or hardware state.

## Baseline prerequisites

- Latest supplied software suite: 42 passed.
- Prior simulation/startup checks: recorded as passed.
- Reviewed clean baseline commit: pending.
- Verified Stage 3 recovery checkpoint: pending.

Baseline completion does not authorize physical motion.
Stage 4 begins with OS-level enumeration under the roadmap.
Serial communication requires the subsequent applicable stage gate.

## Commissioning requirement

Remaining non-web hardware entry points require inventory, central
authorization enforcement, and verification, as recorded in the phase
conclusions. Physical commissioning awaits the deterministic safety gate.
