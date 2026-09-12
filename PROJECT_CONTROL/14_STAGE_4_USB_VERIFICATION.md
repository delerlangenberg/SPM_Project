# Stage 4 — USB Verification

Verified on Spark: 2026-09-12, using OS-level inspection only.

| Device | Alias | Node | VID:PID | Serial |
|---|---|---|---|---|
| Prusa MK4S | /dev/spm-mk4s | /dev/ttyACM0 | 2c99:001a | 13052-4742441644411328 |
| Arduino Mega 2560 | /dev/spm-arduino | /dev/ttyACM1 | 2341:0042 | 442343134343514182D0 |

Both aliases and by-id links resolve. Both use the cdc_acm driver.
Account deler belongs to dialout and has read/write access.

Observed rules: /etc/udev/rules.d/99-spm-devices.rules.
Current permissions: 0666; matching uses VID/PID, not serial number.
Alias uniqueness with additional identical devices has not been tested.

No serial session, G-code, or probe command was issued by this inspection.
Firmware communication and physical readiness are outside this result.
