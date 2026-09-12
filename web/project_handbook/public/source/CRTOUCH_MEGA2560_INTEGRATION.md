# CR Touch and Arduino Mega 2560 Integration

Status: **DESIGN LOCKED — PHYSICAL WIRING NOT YET VERIFIED**

## Architecture decision

The Arduino Mega 2560 Rev3 is the dedicated CR Touch and future instrument-I/O
controller. The Prusa MK4S xBuddy remains the only motion controller. The PC
coordinates both through separate USB serial links.

```text
Prusa MK4S xBuddy <-- USB --> SPM Operator <-- USB --> Mega 2560
                                                      |
                                              protected adapter
                                                      |
                                                   CR Touch
```

The PSoC Edge E84 is no longer the planned direct CR Touch controller. Infineon
documents J14 as depopulated on Rev. A and newer KIT_PSE84_AI boards. The E84
may remain available for later research tasks, but it is outside the CR Touch
safety chain.

## Why Mega 2560 instead of Uno

| Capability | Uno R3 | Mega 2560 Rev3 | Project consequence |
|---|---:|---:|---|
| Digital I/O | 14 | 54 | Mega leaves capacity for interlocks and sensors |
| PWM outputs | 6 | 15 | Mega supports probe plus future timed outputs |
| Analog inputs | 6 | 16 | Mega supports environmental and auxiliary sensing |
| Hardware UARTs | 1 | 4 | Mega separates PC, diagnostics and future instruments |
| Flash | 32 KB | 256 KB | Mega has room for protocol, logging and safety state |
| SRAM | 2 KB | 8 KB | Mega supports buffered measurements and diagnostics |
| Operating logic | 5 V | 5 V | Both fit the CR Touch 5 V control domain |

The Uno is sufficient for a probe-only demonstrator. The Mega is selected
because the project roadmap includes additional instrument I/O and diagnostics.

## Canonical five-wire allocation

This mapping is the project design. Do not solder until the harness continuity
record and adapter checks are complete.

Set the Seeed Studio Base Shield V2 voltage switch to **5V**. Use only the
digital Grove sockets labeled **D2** and **D8**:

| CR Touch wire | Expected function | Base Shield V2 connection | Required interface |
|---|---|---|---|
| Black | +5 V probe power | D2 socket `VCC` | Inline dedicated fuse, reverse-polarity protection and local decoupling |
| Red | Sensor ground | D2 socket `GND` | Adapter ground; common with White |
| Blue | Trigger output | D2 socket Grove White / `D3` | Protected input; polarity and voltage must be measured |
| White | Control/power ground | D8 socket `GND` | Adapter ground; common with Red |
| Yellow | Deploy/stow control | D8 socket Grove Yellow / `D8` | Series protection; default high-impedance until armed |

Leave D2-socket Grove Yellow/`D2`, D8-socket Grove White/`D9`, and D8-socket `VCC`
unconnected. The keyed Grove cable colors remain fixed: Black=GND, Red=VCC,
White=the white signal position, Yellow=the yellow signal position. Use the
signal names printed on this shield to resolve those two signal positions.

```text
Base Shield D2 socket                 Base Shield D8 socket
┌────────┬────────┬──────┬──────┐    ┌────────┬────────┬──────┬──────┐
│  GND   │  VCC   │  D2  │  D3  │    │  GND   │  VCC   │  D9  │  D8  │
│CRT Red │CRT Blk*│  NC  │ Blue │    │CRT Wht │   NC   │  NC  │Yellow│
└────────┴────────┴──────┴──────┘    └────────┴────────┴──────┴──────┘
                         * through protected fused adapter branch
```

Wire colors are not proof of function. Verify continuity from the keyed probe
connector before installing conductors in the adapter.

## Power path

All five probe conductors terminate at a protected two-Grove-plug adapter. The
Black wire does not connect directly to USB wiring or an unprotected jumper.

```text
Mega USB or approved board supply
        |
   Base Shield D2 VCC with switch at 5V
        |
 dedicated probe fuse
        |
 reverse-polarity protection
        |
 local bulk + ceramic decoupling
        |
 CR Touch Black
```

Before powering the probe:

1. Measure the Mega `5V` rail unloaded.
2. Verify the probe branch fuse and polarity.
3. Verify Black-to-Red and Black-to-White voltage at the disconnected probe
   connector.
4. Confirm no continuity from Black to Yellow or Blue.
5. Power with current monitoring and stop on unexpected current or heating.

Do not use an analog, I2C, UART or ISP socket for the CR Touch.

The official Mega documentation specifies a resettable USB polyfuse that opens
above 500 mA. That protects the upstream USB port; the probe branch still
requires its own appropriately selected protection after actual probe current
is measured.

## Reserved expansion resources

- `Serial` / pins `0`, `1`: PC USB protocol.
- `Serial1` / pins `18`, `19`: reserved for a future isolated instrument.
- `Serial2` / pins `16`, `17`: reserved for environmental sensing.
- `Serial3` / pins `14`, `15`: reserved for service diagnostics.
- `D3`: reserved second interrupt/interlock.
- `D10`: reserved timed safety output.
- `SDA/SCL` / pins `20`, `21`: reserved I2C sensor bus.
- `A0`–`A3`: reserved analog instrumentation.

## Prohibited connections

- No Mega connection to xBuddy STEP, DIR, ENABLE, ZL, ZR or J29.
- No CR Touch conductor soldered to USB D+, D-, CC1 or CC2.
- No probe power taken from a signal pin.
- No Real Measurement unlock based only on COM-port detection.
- No use of deploy/stow pulse widths copied from an unverified harness.
