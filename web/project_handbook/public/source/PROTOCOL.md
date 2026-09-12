# SPM Edge Protocol v1

The commissioning transport is newline-delimited ASCII over the KitProg3 UART.
The production transport will use target USB with sequence numbers, device-side
timestamps, length and CRC. Commands are rejected unless the device is in a
compatible state and the host heartbeat is current.

Commands: `HELLO`, `GET_INFO`, `GET_STATUS`, `SELF_TEST`, `DEPLOY`, `STOW`,
`ARM`, `DISARM`, `CLEAR_FAULT`, `GET_DIAGNOSTICS`, `PING`.

`GET_DIAGNOSTICS` is always non-actuating. Before hardware commissioning it
reports board/UART health and explicitly reports the probe tests as
`NOT_TESTED` or `LOCKED`; it must never convert an unmeasured pin into PASS.

`PING` is the non-actuating liveness command. The host must treat missed or
malformed `PONG` responses as transport loss and block new hardware movement.

Events: `READY`, `HEARTBEAT`, `PROBE_DEPLOYED`, `PROBE_STOWED`,
`PROBE_TRIGGERED`, `PROBE_RELEASED`, `FAULT`, `WATCHDOG_RESET`.

Required identity fields: board ID, firmware version, protocol version, serial
number, hardware-lock state and calibration revision.
