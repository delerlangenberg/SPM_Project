# Spark Baseline Validation

Date: 2026-09-12

## Verified results

- Python 3.12.3 on Spark Linux ARM64.
- Exact package snapshot: requirements-spark-pinned.txt.
- Binary installation packages downloaded and checksummed.
- Separate environment installed entirely from local packages.
- Rebuilt package versions matched the snapshot exactly.
- pip check passed.
- Full canonical suite in rebuilt environment: 42 passed.

## Recovery evidence

Local validation directory:
`/home/deler/SPM_Recovery/BASELINE_VALIDATION_20260912_125559_We8irs`

Contains wheels, SHA256SUMS, rebuilt package list, and pytest output.
Recovery requires compatible Linux ARM64, Python 3.12, and system libraries.
The package snapshot does not capture operating-system dependencies.

## Baseline scope

Runtime hardware logs and learning history remain local and excluded from Git.
Existing configuration and legacy tools are retained as migration source;
their inclusion does not authorize hardware operation.
RELEASE_SHA256.csv is historical release evidence, not current source hashes.

## Remaining closeout

Initial baseline commit and verified Stage 3 COMPLETE recovery checkpoint.
Stage 3 remains in progress. Hardware authorization remains blocked.
