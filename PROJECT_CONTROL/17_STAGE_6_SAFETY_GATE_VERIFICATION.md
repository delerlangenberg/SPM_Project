# Stage 6 — Deterministic Hardware Safety Gate Verification

Verified on Spark: 2026-09-12 15:14:00 CEST.
Module: [`core/system/deterministic_safety_gate.py`](file:///srv/doro_lab_projects/apps/spm-prusa/core/system/deterministic_safety_gate.py).

## 1. Safety Policies & Invariants Enforced

### A. Central Command Authority
- All physical motion commands must pass through `DeterministicHardwareSafetyGate`.
- No direct serial write or bypassed execution is permitted.
- Raw forbidden G-codes (`G28`, `G29`, heating `M104`/`M109`/`M140`/`M190`, EEPROM writes `M500`) are rejected and immediately latch a `FAULT`.

### B. Workspace & Coordinate Bounding
- **X Range**: $[20.0, 80.0]\,\text{mm}$ (hard limit)
- **Y Range**: $[20.0, 80.0]\,\text{mm}$ (hard limit)
- **Safe Z Floor Limit**: $Z_{\min} = 120.0\,\text{mm}$ (preventing any downward collision prior to verified physical probe commissioning)
- **Z Max Altitude**: $150.0\,\text{mm}$
- **Feedrate Caps**: Max XY: $50.0\,\text{mm/s}$, Max Z: $10.0\,\text{mm/s}$

### C. Mandatory Arduino Feedback Freshness & Watchdog
- Enforces strict feedback arrival deadline ($250\,\text{ms}$).
- Any missing, stale, or malformed Arduino packet latches a `FAULT` state and aborts motion authorization.
- Latched `FAULT` cannot be cleared by subsequent packets alone; explicit operator acknowledgement (`acknowledge_fault`) and a new preflight are mandatory.
- Zero auto-restart or auto-retract upon lost feedback.

## 2. Test Verification
- Unit & integration tests in [`tests/test_deterministic_safety_gate.py`](file:///srv/doro_lab_projects/apps/spm-prusa/tests/test_deterministic_safety_gate.py):
  - State machine lifecycle (`DISCONNECTED` $\rightarrow$ `READ_ONLY` $\rightarrow$ `PREFLIGHT` $\rightarrow$ `READY` $\rightarrow$ `ARMED` $\rightarrow$ `MOTION_AUTHORIZED`)
  - Watchdog timeout & stale feedback fault latching
  - Bounding envelope & safe Z floor violation rejection
  - Forbidden command filtering
  - Emergency Stop (`E_STOP`) and operator fault acknowledgement
- Total test suite: **72 / 72 passing**.

