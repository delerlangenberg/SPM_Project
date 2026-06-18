# Phase 2.2 Roadmap - Controlled Real Scan Path

Created: 2026-06-18 17:09:09

Starting baseline:
- Phase 2.1 is closed.
- Web console is clean.
- Real hardware read-only connection works.
- Short Health Test works.
- 50% Health Test works.
- Real Safe Retract works.
- Hardware logs are ignored by git.
- Git status was clean before Phase 2.2.

Phase 2.2 goal:
Build a safe real scan pathway from scan parameters to verified hardware motion.

Phase 2.2A:
- Inspect current scan/raster code.
- Identify existing scan profile, scan launch, simulation, and web API paths.
- Decide exact files for the scan executor patch.

Phase 2.2B:
- Add scan safety envelope validation.
- Require safe Z before XY scan movement.
- Block scan if outside configured safe range.

Phase 2.2C:
- Add hardware scan skeleton.
- Move XY raster only at safe Z.
- Do not lower into contact.
- Do not deploy probe.
- Do not heat, home, or write printer settings.

Phase 2.2D:
- Stream scan progress into SPM LIVE LOG.
- Save scan skeleton CSV.
- Save scan path PNG/preview.

Phase 2.2E:
- Add optional sensor placeholder channel.
- Prepare for later CR-Touch/probe/sensor integration.

Rule:
No uncontrolled movement, no homing, no heating, no probing deploy/stow.

Phase 2.2A finding:
- Controlled Z approach to the coin/foam test completed safely.
- M119 did not report contact before the Z floor.
- Therefore M119 must not be used as the STM contact detector.
- Real auto-approach is blocked until a verified sensor/contact channel exists.
