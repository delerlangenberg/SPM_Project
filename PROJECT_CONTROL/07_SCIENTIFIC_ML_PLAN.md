# Scientific and ML Development Plan

## Scientific measurement requirements

Every measurement should eventually store:

- measurement ID;
- sample ID;
- timestamp;
- Git/software version;
- instrument configuration;
- X/Y/Z units;
- scan bounds;
- point spacing;
- scan direction;
- probe state;
- calibration ID;
- raw values;
- processed values;
- processing parameters;
- uncertainty;
- warnings;
- failed points.

## ML measurement-quality layer

Target classifications:

- stable signal;
- excessive noise;
- drift;
- probe instability;
- line artifacts;
- outliers;
- failed scan regions.

## Surface-intelligence layer

Targets:

- segmentation;
- feature detection;
- particle detection;
- edge detection;
- defect detection;
- morphology classification.

## Adaptive scanning

1. perform coarse overview scan;
2. build quantitative quality map;
3. identify features;
4. rank ROI;
5. create refinement proposal;
6. deterministic safety gate validates;
7. operator approves;
8. perform high-resolution scan;
9. compare coarse/refined results.

## ML rule

ML is supplementary scientific evidence.

Calibrated physical quantities remain based on explicit, testable numerical methods.

## DGX Spark GPU targets

- PyTorch inference;
- segmentation;
- anomaly detection;
- feature classification;
- denoising research;
- scan planning;
- multimodal scientific assistance.
