# SPM Prusa — DGX Spark Linux Baseline

Source release:
v1.3.1.0 adaptive object release — 2026-07-31

Verification source:
v1.3.0.0 random object adaptive verified — 2026-07-31

Architecture:
NVIDIA DGX Spark / Linux ARM64

Current migration policy:
- Spark becomes canonical SPM development host.
- Historical milestone backups remain on the former SPM PC.
- Windows virtual environments and installers are not part of the Linux runtime.
- Hardware is not connected during baseline validation.

Scientific modernization target:
- reproducible raw measurement acquisition
- calibration and uncertainty
- quantitative topography
- ML measurement-quality scoring
- ML anomaly / defect detection
- feature recognition
- adaptive ROI selection
- adaptive scan planning
- GPU-assisted analysis
- provenance and experiment metadata

Safety:
AI/ML must never bypass deterministic motion limits or hardware interlocks.
