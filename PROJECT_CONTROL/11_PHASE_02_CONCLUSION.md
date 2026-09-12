# Phase 2 Conclusion: Central Web Motion Lockout

**Completed:** 2026-09-11

## Result

The active web-facing Z, raster, foil-tap, health-motion, safe-standby, and
safe-close motion gates now defer to the safety supervisor. Legacy environment
variables cannot enable physical motion through these paths.

## Verification

- Focused safety and web-lockout tests: **8 passed**.
- Tests explicitly set `SPM_WEB_ALLOW_REAL_SCAN`, `SPM_WEB_ALLOW_Z_MOTION`, and
  `SPM_WEB_ALLOW_HEALTH_MOTION` to `1`; each request was denied before any
  serial connection or hardware command.
- The local operator console exposes the enforced state at
  `/api/safety/status`.
- The browser console renders the Phase 2 supervisor panel with
  `DISCONNECTED`, `Real motion: locked`, `Serial: closed`, and `G-code: none`.
- The launcher now changes to the project root, so configuration-backed
  Z-reference and measurement-limit panels load when the server is started
  outside the project directory.

## Phase Gate

**PASS for central web motion lockout.** Real motion remains disabled.

Phase 3 may add a simulation experiment/run service with immutable raw output
and fault injection. Hardware commissioning remains blocked until every
remaining non-web hardware entry point is inventoried, routed through the same
authority, and verified on a controlled fixture.