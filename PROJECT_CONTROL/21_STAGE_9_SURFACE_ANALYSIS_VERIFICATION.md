# Stage 9 — Scientific Surface Analysis Verification

Verified on Spark: 2026-09-12 15:43:38 CEST.
Framework: [`core/analysis/surface_analysis.py`](file:///srv/doro_lab_projects/apps/spm-prusa/core/analysis/surface_analysis.py).
Runner: [`tools/stage9_surface_analysis_verification.py`](file:///srv/doro_lab_projects/apps/spm-prusa/tools/stage9_surface_analysis_verification.py).
Deliverables Directory: [`data/processed/`](file:///srv/doro_lab_projects/apps/spm-prusa/data/processed/).

## 1. Scientific Surface Metrology Invariants Verified
* **Deterministic Numerical Methods**:
  - Plane leveling ($Z = aX + bY + c$) and polynomial background subtraction ($Z = c_0 + c_1 X + c_2 Y + c_3 X^2 + c_4 Y^2 + c_5 XY$) fitted via least-squares; tilt residuals $< 10^{-12}\,\text{mm}$.
  - Median filtering despiking and artifact rejection validated without non-standard binary dependencies.
* **ISO 25178 / ISO 4287 Quantitative Roughness**:
  - Areal surface parameters verified: $S_a$ (arithmetical mean height), $S_q$ (root-mean-square height), $S_z$ (peak-to-valley), $S_p$ (peak height), $S_v$ (pit depth), $S_{sk}$ (skewness), and $S_{ku}$ (kurtosis).
  - Validated analytically against exact closed-form sinusoidal solutions.
* **Line Profile & Step Metrology**:
  - Bilinear interpolation along arbitrary profile vectors with Euclidean trajectory distance.
  - Step height evaluation across upper and lower terraces with standard error quantification.
* **Particle & Island Feature Segmentation**:
  - 8-connected flood fill segmentation computing particle count, centroid positions ($X, Y$), surface area ($\text{mm}^2$), equivalent diameter, peak/mean height, and volume ($\text{mm}^3$).
* **Publication-Grade 2D / 3D Topography Rendering**:
  - Calibrated false-color 2D map with physical units, scale bars, and colorbar.
  - 3D perspective surface mesh rendering and 1D cross-sectional profile plots.

## 2. Test Verification
* **86 / 86 automated tests passing** (`PYTHONPATH=. .venv/bin/pytest`).
* Validated in [`tests/test_surface_analysis.py`](file:///srv/doro_lab_projects/apps/spm-prusa/tests/test_surface_analysis.py).

