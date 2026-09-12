# Stage 2 LoveBoard Connector Assessment

**Date:** 30 July 2026  
**Decision:** retain the LoveBoard, but do not replace the Arduino Mega with it.

## What the LoveBoard is

Prusa describes the LoveBoard as a proprietary connector breakout that gathers
the extruder cables. It is not a second programmable controller and does not
provide seven interchangeable GPIO ports. Each socket is wired to a dedicated
xBuddy-controlled function.

Official references:

- [Prusa xBuddy and LoveBoard wiring](https://help.prusa3d.com/article/xbuddy-and-loveboard-electronics-wiring-mk4-s-mk3-9-s_413095?product=mk3-9s)
- [Prusa MK4S maintenance guide](https://cdn.help.prusa3d.com/wp-content/uploads/generated/printer-maintenance_247_guide_525274_en_2026-05-13.pdf)
- [Prusa Firmware Buddy source](https://github.com/prusa3d/Prusa-Firmware-Buddy)

## Connector decision matrix

The printed label and official wiring documentation are authoritative. Never
identify a socket from its physical position alone.

| Dedicated function | Electrical character | CR Touch replacement? | Stage 2 decision |
|---|---|---:|---|
| Extruder motor | Bipolar stepper phases from a motor driver | No | Leave disconnected; software blocks E moves |
| Hotend heater | Switched high-current heater output | No | Leave disconnected; command firewall permits only heat-off |
| Hotend thermistor | Biased analog temperature input | No | Open reading is monitored; never fit a dummy resistor to hide it |
| Heatsink thermistor | Biased analog temperature input | No | Reserve only for a documented compatible temperature sensor |
| Print fan | Dedicated fan power/PWM path | No | Leave disconnected; output is forced off |
| Heatsink fan | Dedicated fan power/PWM/tach path | No | Leave disconnected unless cooling is later mechanically required |
| Loadcell / filament-sensor paths | Specialized measurement or logic interfaces | No direct connection | Preserve for a separately designed force-sensing experiment |

Connector counts and grouping can vary by printer revision; this table is
functional, not a pinout. Exact voltage, pin order and signal conditioning must
be established from the correct LoveBoard revision schematic and continuity
measurements before any reuse.

## Why the Mega remains necessary

The current CR Touch interface needs:

- regulated 5 V power and common ground;
- a 50 Hz servo-style control waveform on Mega D8;
- a protected trigger input on Mega D3;
- latched contact capture independent of xBuddy motion;
- LCD/RGB operator feedback and a USB protocol that defaults to safe state.

The LoveBoard supplies none of those functions as a user-programmable module.
Connecting CR Touch to a heater, fan, motor, thermistor or loadcell connector
could damage the probe or xBuddy.

## Recommended future uses

1. Keep the LoveBoard installed as a mechanically convenient, labelled cable
   breakout.
2. Preserve the original loadcell connector for a future calibrated
   force-channel study. Use an external instrumentation amplifier/ADC unless an
   exact Prusa electrical interface is verified.
3. Use a spare thermistor channel only for temperature drift logging with a
   compatible sensor and verified transfer curve.
4. For the next high-resolution instrument, add a dedicated piezo controller,
   low-noise displacement/force sensor and external DAQ. Do not repurpose
   xBuddy safety I/O as general measurement I/O.

## Revisit criteria

This decision may be revisited only after the exact LoveBoard hardware revision
is recorded, official schematics or a complete measured pinout are available,
input/output voltage limits are verified, and a firmware ownership analysis
shows the connector can be isolated without weakening printer safety.
