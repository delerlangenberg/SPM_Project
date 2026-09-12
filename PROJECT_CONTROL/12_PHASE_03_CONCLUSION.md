# Phase 3 Conclusion: Simulation Experiment Evidence and Fault Injection

**Completed:** 2026-09-11

## Result

Phase 3 adds a simulation-only experiment-run service. Each run writes a
manifest, immutable raw JSONL samples, and append-only JSONL events. The
manifest records SHA-256 hashes of both artifacts and declares that no serial
port, G-code, or real motion was used.

The service rejects attempts to reuse a run directory. The web demo may read
and display an existing run manifest, but cannot overwrite its artifacts.

## Fault Injection

`stale_readback` is the first deterministic injected fault. It stops the
synthetic raster halfway through, writes the partial raw dataset, records a
`fault_injected` event, and completes with `FAULTED` status.

## Verification

- Focused experiment artifact tests: **2 passed**.
- Combined safety, web-lockout, experiment, and fault tests: **10 passed**.
- Browser console at `http://127.0.0.1:8787/?phase=3-experiment-runs-20260911`
  displayed a completed run with 32 samples and a SHA-256 raw-data hash.
- The same console displayed the `stale_readback` run as `FAULTED`, retaining
  16 samples and its SHA-256 raw-data hash.
- During both runs, the live safety panel reported `DISCONNECTED`, real motion
  locked, serial closed, and no G-code.

## Phase Gate

**PASS for simulation-run provenance and one injected data-quality fault.**
Real motion remains disabled. The next phase should expand deterministic fault
coverage (disconnect, timeout, invalid sensor value, and over-limit) and bind
run events to the safety-supervisor lifecycle without enabling hardware.