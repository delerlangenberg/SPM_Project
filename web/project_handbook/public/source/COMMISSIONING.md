# Commissioning Procedure

1. Install current ModusToolbox and the official `KIT_PSE84_AI` BSP.
2. Build and flash a vendor GPIO/UART example without the probe attached.
3. Confirm which physical USB-C port is KitProg3 and which is target USB.
4. Select two J14 P16/P17 signals in Device Configurator: one TCPWM output and
   one interrupt-capable input.
5. Verify both physical header pins and logic levels with a meter/scope.
6. Identify every ALT04 harness conductor by connector documentation and bench
   measurement. Record results in `PINOUT_REFERENCE.md`.
7. Power the probe from a current-limited 5 V supply with the xBuddy physically
   disconnected.
8. Measure the sensor released/triggered voltage and polarity.
9. Determine deploy/stow commands from verified CR-Touch documentation or a
   logic-analyser capture; do not use the provisional values from the supplied
   instruction.
10. Assemble and verify the protected adapter.
11. Enter the verified pins/pulses and set `SPM_EDGE_HARDWARE_VERIFIED` to `1`.
12. Test at least 100 manual trigger cycles before mounting on the printer.

Printer motion integration remains step-and-check through the PC and stock
xBuddy USB interface. This firmware never injects an endstop signal.

