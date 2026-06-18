# Phase 2.2B - SPM Scan Method Model

Created: 2026-06-18 17:55:39

Purpose:
Define the real scanning method before implementing scan buttons in the web UI.

Core idea:
The scanner does not create an image in one movement. It creates an image
point-by-point. At each XY pixel, the Z scanner approaches the surface,
a feedback/contact/signal value is evaluated, the point is recorded, and
the scanner moves to the next point.

Important safety conclusion from Phase 2.2A:
- M119 did not detect contact during the coin/foam approach test.
- Therefore M119 is not a valid contact detector for this setup.
- Current approach can only be software-position approach.
- True auto-contact requires a verified feedback channel.

Future feedback channels:
1. Mechanical/contact sensor.
2. Prusa loadcell or probe signal if exposed through usable command/API.
3. STM current threshold.
4. External analog/digital sensor.
5. Any verified sensor that can report contact/setpoint per pixel.

## Point Measurement Model

One point measurement has this sequence:

1. Move XY to target pixel position.
2. Move Z quickly to a guard distance above the expected surface.
3. Move Z slowly in fine steps toward the surface/setpoint.
4. Read feedback after each fine Z step.
5. Stop when feedback condition is reached.
6. Record the measured point:
   - x_mm
   - y_mm
   - z_mm
   - z_above_surface_um
   - feedback value
   - direction
   - line index
   - pixel index
   - timestamp
7. Retract or return to safe clearance.
8. Move to the next XY pixel.

Current test mode:
- Because no real feedback channel is verified yet, software approach stops
  at a declared Z clearance above the expected surface.
- This is useful for motion development but not yet real STM/AFM feedback.

## Raster Scan Direction Model

Fast-axis X scan:
- For each Y line:
  - scan X from x_min to x_max: this creates X+ trace data.
  - scan X from x_max to x_min: this creates X- retrace data.
  - move Y one step.
- Result:
  - X+ topography image.
  - X- topography image.

Fast-axis Y scan:
- For each X column:
  - scan Y from y_min to y_max: this creates Y+ trace data.
  - scan Y from y_max to y_min: this creates Y- retrace data.
  - move X one step.
- Result:
  - Y+ topography image.
  - Y- topography image.

Full four-image mode:
- Run fast-axis X scan to get X+ and X-.
- Run fast-axis Y scan to get Y+ and Y-.
- The four directional images can be compared to estimate backlash,
  drift, hysteresis, and direction-dependent artifacts.

## Prusa MK4S Motion Resolution Model

Observed from M114 logs:
- X: 125.00 mm -> Count X: 12500
- Y: 105.00 mm -> Count Y: 10500
- Z: 150.00 mm -> Count Z: 60000

Therefore current firmware coordinate scale is:
- X: 100 counts/mm = 10 um/count.
- Y: 100 counts/mm = 10 um/count.
- Z: 400 counts/mm = 2.5 um/count.

Software rule:
- Requested X/Y pixel coordinates should be rounded to 10 um.
- Requested Z coordinates should be rounded to 2.5 um.
- Display both requested position and rounded executable position.

Important limitation:
This is motor/firmware step resolution, not true imaging resolution.
Real imaging quality will also depend on probe geometry, sensor feedback,
mechanical stiffness, backlash, vibration, foam/sample deformation, and
calibration.

## Scan Size, Resolution, and Pixel Pitch

For a scan area:
- x_range_mm = x_max - x_min
- y_range_mm = y_max - y_min
- nx = number of X points
- ny = number of Y points

Pixel pitch:
- x_step_mm = x_range_mm / (nx - 1)
- y_step_mm = y_range_mm / (ny - 1)

Display:
- x_step_um = x_step_mm * 1000
- y_step_um = y_step_mm * 1000

Validation:
- x_step_um should be >= 10 um.
- y_step_um should be >= 10 um.
- z_step_um should be >= 2.5 um.

## Live Visualization Requirements

The web UI needs two live visual windows:

1. Live line scan window:
   - Always shows the current finished line.
   - Updates after each X+ line and X- line.
   - In Y-fast mode, updates after each Y+ and Y- line.

2. Accumulating topography image:
   - Updates after every completed line.
   - At the end of the scan it becomes the final image.
   - Four-image mode stores:
     - image_x_plus
     - image_x_minus
     - image_y_plus
     - image_y_minus

## CSV Data Model

Each recorded point should store:
- scan_id
- pass_axis
- direction
- line_index
- point_index
- x_mm
- y_mm
- z_measured_mm
- z_above_surface_um
- feedback_value
- approach_status
- timestamp

## Time Estimate Model

Estimated points:
- X-fast trace/retrace points = ny * nx * 2
- Y-fast trace/retrace points = nx * ny * 2
- Full four-image mode = nx * ny * 4

Estimated time:
- time_per_point = approach_time + feedback_time + retract_time + xy_move_time
- total_time_seconds = total_points * time_per_point

The UI should display:
- scan area in mm
- pixel size in um
- number of points
- number of directional images
- estimated time
- expected output CSV and image files

## Phase 2.2 Implementation Order

Phase 2.2B:
- Implement scan-parameter model.
- Compute pixel pitch and Prusa-rounded coordinates.
- Compute estimated scan time.
- Generate raster preview.
- No hardware movement.

Phase 2.2C:
- Implement software Z approach as a reusable module.
- Add Z feedback display:
  - real Z position
  - Count Z
  - um above declared surface
  - target clearance
  - rounded executable Z

Phase 2.2D:
- Implement hardware scan skeleton:
  - XY raster movement at safe height
  - software Z approach per point
  - CSV point recording
  - live line update
  - no real contact claim

Phase 2.2E:
- Add verified sensor feedback channel.
- Convert software-position approach into real feedback approach.
- Enable real contact/setpoint point measurement only after validation.
