# Phase 2.2 Roadmap - Z Scanner Control and Live Feedback

Updated: 2026-06-18 19:06:52

Corrected scope:
Phase 2.2 is only about the Z scanner.

Phase 2.2 goal:
Build a safe, visible, and configurable Z-scanner control layer before
any real XY scan measurement is allowed.

Phase 2.2A:
- Controlled Z auto-approach test.
- Result: Z movement and retract worked.
- M119 did not detect contact.
- M119 must not be used as contact feedback.

Phase 2.2B:
- Software-position Z approach model.
- User defines expected surface Z.
- User defines clearance above surface in micrometers.
- System computes target Z.
- System rounds target Z to Prusa Z resolution.

Phase 2.2C:
- Z scanner parameter UI:
  - surface Z
  - clearance µm
  - fast guard distance
  - fine step µm
  - retract Z
  - feedrates

Phase 2.2D:
- Live Z feedback window:
  - current Z mm
  - Count Z
  - Prusa Z resolution
  - µm above declared surface
  - target clearance
  - rounded executable Z

Phase 2.2E:
- Safe software Z approach button in the web UI.
- No X/Y raster scan.
- No contact claim unless a verified sensor channel exists.

Blocked until later:
- Real contact detection.
- STM feedback.
- XY raster scan.
- Topography image generation.

Moved to Phase 2.3:
- scan planner
- raster preview
- X+ / X- / Y+ / Y- images
- scan-time estimate
- line accumulation
