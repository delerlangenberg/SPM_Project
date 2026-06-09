## SPM Roadmap (Prusa MK4S Integration Phase)

### Phase 1: Hardware Bring-Up (Now)
- Confirm Prusa MK4S mechanical assembly is complete
- Verify USB serial connection from control host (`/dev/ttyACM*` or `/dev/ttyUSB*`)
- Validate backend connect/disconnect without motion
- Validate explicit `G28` homing and bounded `G1` moves

Exit criteria:
- Stable serial session
- Repeatable home operation
- No unexpected movement during connect

### Phase 2: Motion Safety and Limits
- Define SPM-safe motion envelope (X/Y/Z limits)
- Enforce software limits in motion command path
- Add emergency-stop drill and recovery procedure

Exit criteria:
- Motion command outside bounds is rejected
- E-stop behavior is documented and tested

### Phase 3: Z-Control Coupling
- Integrate Arduino Z-control feedback with motion workflow
- Add polling/state readback during scan steps
- Validate approach/retract sequence at low speed

Exit criteria:
- Controlled approach without tip crash
- Stable Z feedback at fixed XY point

### Phase 4: First Real Scan
- Execute low-resolution raster test over a calibration surface
- Save raw scan data and metadata
- Render first heatmap and verify coordinate mapping

Exit criteria:
- One successful physical scan end-to-end
- Reproducible map geometry across repeated runs

### Phase 5: Reliability and Repeatability
- Run 10 repeated scan cycles
- Track drift, backlash effects, and failed commands
- Tune feedrate/acceleration for stable operation

Exit criteria:
- Repeatability metrics documented
- Baseline operating profile approved for student use
