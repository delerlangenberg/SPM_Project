# Target Architecture

## High-level architecture

Operator UI / Dashboard
        |
        v
SPM Application / API
        |
        +---- Scientific Analysis
        |       - calibration
        |       - topography
        |       - filtering
        |       - roughness
        |       - uncertainty
        |
        +---- ML Layer
        |       - quality scoring
        |       - anomaly detection
        |       - feature recognition
        |       - ROI recommendation
        |
        v
Deterministic Safety Gate
        |
        v
Hardware Abstraction
      /     \
     v       v
 Prusa     Arduino
 MK4S      Probe

## Core principle

AI/ML may recommend.

AI/ML may not directly authorize or execute unsafe motion.

All real hardware commands must pass through deterministic limits, calibration checks, interlocks and operator authorization.

## Data flow

Raw acquisition
→ immutable raw dataset
→ calibration
→ preprocessing
→ processed dataset
→ quantitative analysis
→ ML interpretation
→ adaptive recommendation

Raw data must never be overwritten by processed data.
