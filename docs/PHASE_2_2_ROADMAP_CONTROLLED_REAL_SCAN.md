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

Phase 2.2B model correction:
- The scan is point-based, not image-based.
- Each pixel requires Z approach, feedback/readout, recording, and movement.
- X-fast scan produces X+ and X- directional topography images.
- Y-fast scan produces Y+ and Y- directional topography images.
- Full four-image mode requires both X-fast and Y-fast passes.
- Live UI must show the current line and accumulating image after each line.
- M119 is not a valid contact detector from Phase 2.2A.
- Until a feedback channel is verified, approach is software-position only.
