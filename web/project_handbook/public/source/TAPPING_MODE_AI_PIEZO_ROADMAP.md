# Tapping Mode, AI, and Piezo Roadmap

## Current validated result

The CR Touch completed a one-contact-per-speed characterization at 0.05,
0.10, 0.20, 0.40, and 0.80 mm/s using 0.05 mm Z steps. Every trial detected
Z17.600. This proves no detected shift in this small experiment; it does not
yet certify the fastest speed for unknown surfaces.

## Unknown-surface tapping policy

Unknown surfaces always begin with the slowest conservative approach and a
deterministic hard floor. Speed can increase locally only after repeatable
contacts establish a safe height envelope. XY motion occurs with the probe
stowed. Missing contact, stale transport, abnormal edge count, drift, or
temperature concern causes retract and abort.

## AI role

AI predicts likely geometry and an uncertainty map from camera images,
previous lines, neighboring measurements, and known machine geometry. Active
sampling prioritizes boundaries, high uncertainty, and verification points.
AI never commands motion outside the deterministic safety envelope. Every map
pixel is tagged as measured, interpolated, or AI-predicted.

## Sensor fusion

A global-shutter camera with a telecentric lens provides coarse XY boundary
location, feature recognition, spacer/sample registration, and collision
context. It is not the Z metrology sensor. The fine stage requires direct
position metrology and a real interaction sensor such as an AFM cantilever,
piezoresistive cantilever, tuning fork, or equivalent force-gradient sensor.

## Recommended piezo path

The practical Step 2 stage is the PI P-616.3C: closed-loop XYZ, 100 micrometers
per axis, parallel kinematics, and direct capacitive position sensing. It gives
enough capture range to integrate with the Prusa coarse stage.

For a later small-field, high-speed SPM head, use the PI P-363.3CD PicoCube
with its matched E-536 controller. Its much smaller 5 micrometer XYZ range is
appropriate only after coarse positioning and approach are mature.
