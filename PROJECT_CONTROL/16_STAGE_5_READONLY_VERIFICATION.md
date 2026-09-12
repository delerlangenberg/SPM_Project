# Stage 5 — Read-Only Hardware Communication Verification

Verified on Spark: 2026-09-12 15:12:00 CEST.
Mode: **Strict Read-Only Inspection (Zero Motion / Zero Actuation)**.

## 1. Prusa MK4S Read-Only Telemetry (`/dev/spm-mk4s` -> `/dev/ttyACM0`)
- **Firmware**: `Prusa-Firmware-Buddy 6.2.4+8909 (Github)`
- **Machine Type**: `Prusa-MK4`
- **Temperatures (`M105`)**: Hotend: `-20.00°C` (unconnected thermistor baseline), Bed: `24.85°C`, Ambient: `37.65°C`
- **Endstops (`M119`)**: `x_min: open`, `x_max: open`, `y_min: open`, `y_max: open`, `z_min: open`, `z_max: open`
- **Current Coordinates (`M114`)**: `X:14.00 Y:-4.00 Z:120.00`
- **Motion Commands Issued**: **0** (All `G0`, `G1`, `G28`, `G29` filtered and prohibited)
- **Log Files**:
  - `docs/hardware_logs/SPM_20260912_151209_B63D3A_phase_2_2c_on_connect_readonly.txt`
  - `docs/hardware_logs/SPM_20260912_151209_B63D3A_phase_2_2c_on_connect_readonly.jsonl`

## 2. Arduino Mega 2560 Probe Controller (`/dev/spm-arduino` -> `/dev/ttyACM1`)
- **Identity**: `SPM_PROBE_MEGA2560`
- **Firmware**: `0.8.7-fast-tap` (Protocol v1)
- **Wiring Revision**: `GROVE_BASE_V2_D3_D8`
- **Hardware Verified**: `true`
- **Calibration Revision**: `CRT-D3-D8-5OF5`
- **State**: `READY`
- **Trigger Raw**: `false` (No false triggers observed)
- **Actuation Locked**: `true`
- **Self-Test**: `PASS`
- **Actuation Attempted**: `false`

## 3. Incident Containment Verification
- Direct Z execution and calibration endpoints remain hard-blocked in source.
- Automated test suite passed 66/66 tests (`PYTHONPATH=. .venv/bin/pytest`).

