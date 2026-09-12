# Hardware Safety Gate — Incident Hold

Physical operation and new serial sessions are BLOCKED.
The earlier Stage 5 live button-test exception is revoked.

Reason: the operator reported calibration driving Z downward without
Arduino feedback and nearly damaging the CR-Touch.

Known calibration backend entry points are blocked in source.
Three entry points have been tested to reject before serial access.
These results do not establish that every motion path is protected.

Current work: offline source review, mocked tests, and incident evidence.
Do not trust the changed calibration record pending investigation.
Existing application processes may still contain the pre-patch code.

Reopening hardware access requires a reviewed procedure with verified
central motion authorization, probe feedback, stale-feedback handling,
travel limits, and stop behavior. A UI authorization label is insufficient.
