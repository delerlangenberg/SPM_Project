# Hardware Safety and USB Gate

## Authorization

Physical operations and serial communication remain BLOCKED.

After the recovery marker specified in 01_CURRENT_STATUS.md exists,
Stage 4 permits OS-level USB enumeration only: lsusb, device listings,
and udevadm identity/permission inspection.

Do not issue G-code, actuate the probe, home, calibrate, or scan.
Do not infer current position or readiness from historical records.
This documentation does not modify runtime interlocks.

## Subsequent gates

Serial communication requires Stage 5 authorization.
Physical commissioning requires the deterministic safety gate and
verification of remaining non-web hardware entry points.
