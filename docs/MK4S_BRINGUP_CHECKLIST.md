## MK4S Bring-Up Checklist for SPM

Use this checklist when starting hardware integration sessions.

### A. Pre-Flight Safety
- Confirm probe/tip is protected before any motion test
- Keep hand near power-off and emergency-stop controls
- Start with low feedrate for all manual tests
- Clear cable routing to avoid snags during XY travel

### B. Host and Serial Link
- Connect MK4S via USB to control host
- Identify serial port:
  - `ls /dev/ttyACM* /dev/ttyUSB* 2>/dev/null`
- Confirm user has serial permissions (`dialout` group)
- Verify port can be opened by backend without motion

### C. Controlled Motion Validation
- Run absolute mode command (`G90`)
- Run homing (`G28`) with clear workspace
- Test bounded moves:
  - small +X / -X
  - small +Y / -Y
  - optional small +Z / -Z (safe range only)
- Validate no drift while idle

### D. SPM Envelope Definition
- Record allowed X/Y travel for SPM fixture
- Record safe Z range for approach/retract
- Store limits in configuration used by motion backend
- Verify out-of-range commands are blocked

### E. Z-Control Integration Readiness
- Confirm Arduino link is stable
- Confirm Z-control readback is visible in logs/state
- Test approach and retract sequence at one fixed XY point

### F. First Scan Readiness Gate
Proceed to first scan only if all are true:
- Serial stability: pass
- Home repeatability: pass
- Limit checks: pass
- Z-control basic sequence: pass

### G. Session Log Template
- Date/time:
- Operator:
- Serial port used:
- Homing result:
- Motion test result:
- Z-control test result:
- Issues found:
- Next action:
