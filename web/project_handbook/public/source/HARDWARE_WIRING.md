# Hardware Wiring — Commissioning Only

## Prohibited connections

- Never connect the PSoC or CR-Touch to xBuddy ZL or ZR. They are stepper-motor
  outputs, not endstop inputs.
- Never solder PSoC GPIO to MiniBuddy or xBuddy stepper-driver STEP, DIR, or
  ENABLE nets. Firmware port names such as `PD4` are MCU net names, not
  supported external control headers, and this project uses an MK4S/xBuddy,
  not a Prusa MINI/MiniBuddy.
- Never connect an unknown probe signal directly to a PSoC input.
- Never identify ALT04 functions from wire colour alone.
- Never splice a USB cable by conductor colour.

## Required interface

Use a small protected adapter between J14 and the probe:

- separately fused, regulated 5 V probe supply;
- 74AHCT-family 5 V control buffer driven by a verified J14 output;
- sensor conditioning to a verified 3.3 V J14 input;
- series resistance, ESD protection, decoupling, keyed connectors, and test
  points.

The xBuddy and PSoC communicate only through the coordinating PC software over
their separate USB connections.

## Verified system communication architecture

| Link | Physical connection | Purpose |
|---|---|---|
| PC to Prusa MK4S | Prusa USB, currently `COM6` | Authorized G-code motion and printer status |
| PC to PSoC E84 | Separate USB cable to E84 `J1` KitProg3 | Programming plus commissioning UART |
| PSoC E84 to CR Touch | J14 through protected adapter | Probe control and conditioned trigger only |
| PSoC E84 to xBuddy | **No electrical connection** | Coordination occurs in PC software |

The E84 `J2` target USB connector is reserved for a future production USB
device implementation. It is not the initial programming connector.
