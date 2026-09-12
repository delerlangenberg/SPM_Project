# SPM Operator v1.3.1.0

**Release date:** 31 July 2026

## Adaptive object discovery

This release promotes the physically validated overview-to-focus workflow into
the normal operator software.

- **Discover & Refine Objects** replaces the fixed two-object wording.
- Balanced is the default: 20 mm whole-field overview followed by 5 mm local
  refinement.
- Precision uses 20 mm → 2.5 mm; Research uses 15 mm → 1 mm.
- Spatial connected components discover one to 12 separated raised regions.
- More than 12 regions fails closed.
- The existing mount, thermal, authorization, trigger and safe-retract gates
  remain mandatory.

The workflow is calibrated for raised objects approximately 9.5–12.0 mm above
the stage. It is not yet an arbitrary-height unknown-surface approach.

## Physical validation

Two randomly placed 29.3 mm × 11.3 mm magnets were found without supplied
coordinates. The run completed 143 overview readings, 128 focused readings and
62 contacts. Centers were X80.50/Y87.50 and X185.50/Y132.50.

See `docs/STAGE2_RANDOM_TWO_MAGNET_TEST_20260731.md`.

## Verification

- 360 Python tests passed.
- Local handbook production build passed.
- Two handbook/browser checks passed.
- Canonical installer built successfully; SHA-256:
  `4F195548E1BD7FF1B96B52CAE9BCAEA78F7EA1BA46629D64CA36DB0E1E32B2C4`.
- Silent installed upgrade exited successfully.
- Installed application launched outside the source tree and remained healthy
  for the smoke-test window.
- Installed file, product and registry versions all report 1.3.1.0.
- Final hardware audit: X168/Y150/Z45, Probe In, Mega READY, D3 LOW, D8
  high-impedance and heater targets/outputs zero.
