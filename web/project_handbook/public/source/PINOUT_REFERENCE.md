# Pinout Reference

Board: `KIT_PSE84_AI`, PCB `600-60751-01`, schematic `630-60751-01 Rev 03`.

The official schematic identifies J14 as a 20-pin 100-mil expansion header.
It exposes 3.3 V-compatible translated signals associated with P16/P17 and a
single input-only translated P11.1 signal. Do not infer pin functions from the
photograph alone.

## Commissioning record

| Item | Verified value | Evidence/date |
|---|---|---|
| J14 control output pin | UNVERIFIED | — |
| J14 sensor input pin | UNVERIFIED | — |
| Sensor active polarity | UNVERIFIED | — |
| Sensor released voltage | UNVERIFIED | — |
| Sensor triggered voltage | UNVERIFIED | — |
| Deploy pulse | UNVERIFIED | — |
| Stow pulse | UNVERIFIED | — |
| Harness pin order | UNVERIFIED | — |

## Proposed software assignment (firmware remains locked)

| Purpose | J14 physical pin | MCU/BSP token | Direction | Connection |
|---|---:|---|---|---|
| CR Touch control | 6 | `P16_0` | PWM output | Through 74AHCT 3.3 V-to-5 V buffer to Yellow |
| CR Touch trigger | 13 | `P11_1` | Input only | From Blue through 3.3 V sensor conditioning |
| Common ground | 20 | `GND` | — | Adapter ground; joins White and Red returns |
| Probe power | **not J14** | — | — | Black from separately fused/current-limited regulated 5 V |

`SPM_EDGE_HARDWARE_VERIFIED` remains `0`. J14 pin 19 is 3.3 V and must not
power the 5 V probe.

## Expected five-color CR Touch harness

The official Creality manual shows the probe-connector conductor order as
Blue, Red, Yellow, Black, White. For the common harness with exactly that order,
the expected functions are:

| Color | Expected function | Adapter destination |
|---|---|---|
| Blue | Probe trigger output | Condition to <=3.3 V, then J14 pin 13 / `P11_1` |
| Red | Trigger/sensor ground | Adapter common ground |
| Yellow | Deploy/stow PWM control input | Buffered 5 V control from J14 pin 6 / `P16_0` |
| Black | +5 V probe power | Separate fused/current-limited regulated 5 V |
| White | Control/power ground | Adapter common ground |

Creality harness revisions have been reported with different colors. Confirm
that the connector order physically matches the official Blue-Red-Yellow-Black-
White drawing and verify voltages before attaching the probe.

## One-by-one commissioning order

1. Keep the CR Touch unplugged and `SPM_EDGE_HARDWARE_VERIFIED=0`.
2. Confirm J14 pin 20 is ground and pin 19 is 3.3 V. Do not use pin 19 for probe power.
3. Configure/measure J14 pin 6 as a 3.3 V control output only; verify the protected adapter produces the required 5 V-domain PWM at its Yellow test point.
4. With the separate 5 V supply OFF, connect White and Red to adapter common ground.
5. Current-limit the separate 5 V supply, connect Black to +5 V, then power the probe. Stop immediately on excessive current or fault indication.
6. Connect Yellow to the adapter control output and test stow/deploy while the probe is clear of the printer.
7. Measure Blue relative to Red in released and manually triggered states. Connect it to the conditioning input only after its PSoC-side test point is proven <=3.3 V.
8. Connect the conditioned trigger to J14 pin 13 and verify repeated input transitions before enabling motion.

`P6_2`, `P6_3`, and `P6_4` from the supplied instruction are not accepted:
P6 is a 1.8 V domain on this kit and those placeholders were not established as
J14 signals.

## Rejected MiniBuddy direct-drive proposal

The proposed `P9.0 -> PD4 STEP`, `P9.1 -> PD15 DIR`, and `P9.2 -> PD2 ENABLE`
connections are not part of this design:

- the installed printer is an MK4S with xBuddy, not a MINI with MiniBuddy;
- P9 is a 1.8 V domain on `KIT_PSE84_AI` and is not exposed on J14;
- Prusa firmware MCU port definitions do not establish safe external solder
  points or authorize a second controller to drive the stepper driver's nets;
- independently driving internal motion nets would bypass xBuddy motion state,
  limits, fault handling, and the project's safe-close procedure.

The PC is the sole coordinator. It sends authorized motion to the MK4S over its
USB serial interface and reads the PSoC over a separate USB/KitProg3 UART link.
