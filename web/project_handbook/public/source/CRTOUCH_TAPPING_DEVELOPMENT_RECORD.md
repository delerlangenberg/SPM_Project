# CR Touch Tapping and Adaptive Profiling Development Record

**Record date:** 28 July 2026  
**Status:** Validated coarse-contact research workflow  
**Scope:** Arduino Mega 2560, Grove Base Shield, CR Touch, MK4S motion,
Grove LCD, and Grove Chainable RGB LED

## Record authority and future interface

This maintained handbook record is authoritative for CR Touch development,
evidence, limitations, and accepted operating decisions. The current local
webpage is a readable demonstration of selected material.

The planned operator webpage will later connect to the software for:

- live measurement and machine-state display;
- plots, maps, and analysis;
- protocol and evidence browsing; and
- explicitly authorized operator commands.

Measurement data must originate from the validated acquisition layer. Analysis
must preserve raw data and provenance. Hardware commands must remain fail-closed,
visibly identify their mode, and require the same motion and probe safety checks
as the desktop software.

## 1. Engineering classification

The CR Touch is validated as a coarse contact, tapping-development, boundary
detection, and safety probe. It is not a continuous force sensor and it is not
a micron- or nanometer-resolution SPM probe.

Every result must distinguish:

- **Measured:** a physical CR Touch contact or verified no-contact safety-floor
  result.
- **Interpolated:** a value generated between physical measurements.
- **Predicted:** an AI estimate that still requires uncertainty and verification.

## 2. Validated hardware

| Component | Validated allocation |
|---|---|
| Arduino | Mega 2560 Rev3, COM8 |
| Printer | Prusa MK4S xBuddy, COM6 |
| CR Touch trigger | Mega D3 through Grove D2 White |
| CR Touch control | Mega D8 through Grove D8 Yellow |
| Probe power | Grove D2 VCC, protected 5 V branch |
| Grounds | Grove D2 and D8 GND, common |
| LCD | Grove I2C, address 0x3E |
| RGB indicator | Grove D6/D7 |

Canonical Grove convention: Black is GND, Red is VCC, White is the second
signal/SDA, and Yellow is the first signal/SCL. Printed socket labels still
take precedence over assumptions.

## 3. Commissioning sequence and evidence

1. Passive D3 diagnostics proved trigger readability.
2. D8 was self-measured at 50 Hz with deploy, stow, and reset pulse widths.
3. Corrected socket discovery established that Grove D8 Yellow is Mega D8;
   Grove White is D9 and is not the CR Touch control conductor.
4. Reset/stow/deploy testing produced physical probe motion and D3 edges.
5. Firmware `0.7.1-D3-D8-five-cycle` passed five of five manual trigger cycles.
6. Mounted approach testing confirmed physical contact, automatic retraction,
   RGB/LCD feedback, nozzle clearance, and cool final temperature.
7. Firmware `0.8.5-lcd-rgb-approach` added persistent trigger latching,
   operator display feedback, and safe RGB states.

Important failure lessons:

- A HIGH D3 baseline after a previous touch requires RESET then STOW; STOW
  alone is insufficient.
- A long Z move can exceed a software wait timeout even when motion is healthy.
  Motion timeout must be derived from distance and feed or use a conservative
  upper bound.
- XY calibration belongs to the CR Touch pin, not the nozzle. Visual centering
  and measured edge symmetry refined the probe reference from X125.0 to
  approximately X125.5 at Y105.0.
- Missing contact at a hard floor is a valid boundary result or safe abort,
  never permission to descend farther.

## 4. Mounted Z evidence

Initial mounted testing on the insulated whiteboard magnet found:

| Event | Approximate Z |
|---|---:|
| First physical pin contact | 18.7–18.9 mm |
| Electrical D3 trigger | 16.9–17.6 mm, dependent on reset state and run |
| Observed pin travel before electrical trigger | About 2 mm |
| Safety floor used in profiling | 16.2 mm |
| Local retract | 19.7 or 25.0 mm |
| Full safe retract | 120.0 mm |

The spread in electrical trigger Z is why the CR Touch is classified as a
coarse tapping probe. It must not be used to claim micron surface resolution.

## 5. One-dimensional profile

Target: insulated whiteboard magnet, 29.2 mm outside diameter, about 10.8 mm
high, flat top with approximately 1 mm tapered rim.

The accepted 40-reading path was center-to-left, center repeat, then
center-to-right. Signed distance was referenced to the probe center.

Results:

- Flat top remained near Z17.50–17.60.
- Left taper: Z17.20 at -13.0 mm, Z16.80 at -13.6 mm, and Z16.60 at -14.0 mm.
- Right taper produced a smaller Z17.40 result at +14.0 mm.
- Center repeat difference was 0.05 mm.
- Edge asymmetry indicated an X-center correction of roughly +0.5 mm.

![Center-referenced CR Touch line profile](../web/project_handbook/public/project/crtouch-1d-profile.png)

Data:
`data/crtouch_profiles/magnet_1d_40pt_20260728_173912.csv`

## 6. Adaptive 40 × 40 mm map

A literal 40 × 40-point raster would require 1,600 probe cycles. The accepted
adaptive method used an interior grid, dense polar taper rings, and outside
control points. Redundant far-outside square points were removed after the
first cooling checkpoint.

| Metric | Result |
|---|---:|
| Physical measurements | 116 |
| Contact results | 85 |
| Verified no-contact results | 31 |
| Display projection | 40 × 40 pixels |
| Physical-cycle reduction | 13.8× |
| Fast Z bins | 0.2 mm |
| Final safety position | Z120 |

The displayed map overlays every physical contact and no-contact point.
Distance-weighted height interpolation and an angular boundary derived from
measured rim samples generate the projected pixels. The projection is not
1,600 physical measurements.

![Adaptive measured-point 2D map](../web/project_handbook/public/project/crtouch-adaptive-2d-map.png)

Data:
`data/crtouch_profiles/magnet_adaptive_2d_20260728_175549.csv`

## 7. Tapping speed characterization

One center contact was performed at each speed while retaining 0.05 mm
step-and-check motion.

| Approach speed | Trigger Z | Approach-loop time |
|---:|---:|---:|
| 0.05 mm/s | 17.600 mm | 4.536 s |
| 0.10 mm/s | 17.600 mm | 2.570 s |
| 0.20 mm/s | 17.600 mm | 1.572 s |
| 0.40 mm/s | 17.600 mm | 1.062 s |
| 0.80 mm/s | 17.600 mm | 0.817 s |

The one-iteration result identifies 0.80 mm/s as the fastest candidate on a
known surface. It does not certify that speed for unknown surfaces. Unknown
surfaces begin at 0.05 mm/s and may accelerate only after repeatable local
contacts establish a deterministic Z envelope.

![CR Touch speed sweep](../web/project_handbook/public/project/crtouch-speed-sweep.png)

Data:
`data/crtouch_profiles/crtouch_speed_sweep_20260728_182457.csv`

## 8. Unknown-surface feedback loop

1. Start above the global safe envelope with the probe stowed.
2. Use camera context and prior measurements only to propose candidate features.
3. Perform the first local contact at the slowest speed.
4. Update local height, slope, drift, and uncertainty.
5. Increase tapping speed only where neighboring contacts agree.
6. Sample boundaries and high-uncertainty regions more densely.
7. Insert verification taps in apparently predictable regions.
8. Retract and abort on missing contact, abnormal baseline, transport loss,
   temperature concern, or safety-floor violation.

AI may select the next safe measurement point, but deterministic code owns
the Z floor, maximum step, speed ceiling, retract, and fault behavior.

## 9. Development and purchasing roadmap

### Recommended first fine stage

**PI P-616.3C NanoCube** is the preferred Step 2 stage:

- closed-loop XYZ;
- 100 µm travel per axis;
- direct capacitive position metrology;
- parallel kinematics;
- typical Z bidirectional repeatability of 10 nm.

Official product:
<https://www.pi-usa.us/en/products/piezo-flexure-nanopositioners/xyz-piezo-flexure-nanopositioning-stages/p-616-nanocube-nanopositioner-201751/>

### Premium small-field SPM scanner

**PI P-363.3CD PicoCube with E-536 controller** is the later high-speed,
small-field option. Its 5 × 5 × 5 µm travel, capacitive parallel metrology,
and sub-nanometer positioning are appropriate after coarse positioning is
mature.

Official overview:
<https://www.pi-usa.us/en/news-events/news/afm-xyz-stage>

### Coarse vision

Recommended camera class: global-shutter USB3 machine-vision camera with a
telecentric lens, rigid mount, and controlled ring or coaxial illumination.
The Basler daA2448-70um is a suitable example. Vision supplies XY registration,
feature priors, and collision context; it is not the Z metrology sensor.

Official specifications:
<https://docs.baslerweb.com/daa2448-70um>

### Fine interaction sensor

The final head requires an AFM-style cantilever, piezoresistive cantilever,
tuning fork, or equivalent force-gradient sensor. Existing 5 kg load cells are
useful for macro force experiments but are not suitable for micron/nanometer
SPM feedback. A capacitive displacement sensor can add stage or conductive
target metrology, but does not replace the interaction probe.

## 10. Next experiment: two-object discovery

Keep the current spacer at the calibrated center X125.5/Y105. Place the second
29.2 mm spacer directly left with a measured 10.0 mm edge-to-edge gap. The
nominal second center is X86.3/Y105, but discovery software must not use that
value as a detected result.

The discovery field must cover both objects and empty control space. The
software will:

1. begin with sparse, slow, safe taps;
2. infer candidate occupied regions;
3. concentrate samples around new boundaries;
4. separate the two connected components;
5. estimate each center, diameter, rim, and uncertainty;
6. verify both objects with independent taps;
7. retain measured, interpolated, and predicted labels.

## 11. Two-object 100 × 100 mm real scan — completed

**Run:** 28 July 2026  
**Result:** PASS  
**Acquisition mode:** real hardware, adaptive feedback  
**Authorized field:** X45.5–145.5 mm, Y55.0–155.0 mm  
**Safe final state:** CR Touch stowed; MK4S verified at Z120.00 mm

The operator placed a second nominally 29.2 mm spacer to the left of the
original spacer with a requested 10 mm clear edge gap. Detection did not use
the nominal X86.3 placement coordinate. The software first searched the common
Y105 centerline across the 100 mm field, separated the contact samples into two
components, refined all four transitions at 0.5 mm spacing, and then applied
the validated adaptive 2D pattern around both detected centers.

### Acquisition settings and evidence

| Item | Verified value |
|---|---:|
| Physical measurements | 234 |
| Contacts | 193 |
| No-contact controls | 41 |
| Maximum approach speed | 0.80 mm/s |
| Z command increment | 0.05 mm |
| Left detected center | X85.50, Y105.00 mm |
| Right detected center | X125.75, Y105.00 mm |
| Center separation | 40.25 mm |
| Directly bracketed clear gap | 10.0–11.0 mm |
| Gap midpoint estimate | 10.5 mm |
| Known-diameter gap estimate | 11.05 mm |

The line refinement measured the last left contact at X100.0, the first
intervening no-contact at X100.5, the last no-contact at X110.5, and the first
right contact at X111.0. Therefore the contact/no-contact evidence directly
brackets the clear edge gap between 10.0 and 11.0 mm; its 10.5 mm midpoint is
the preferred result at the present 0.5 mm lateral transition resolution.

The left object had a median trigger Z of 17.00 mm (range 16.20–17.10 mm).
The right object had a median trigger Z of 17.55 mm (range 16.40–17.75 mm).
The approximately 0.55 mm median difference proves the system measured two
physically different surfaces instead of copying a circular template.

![Two-object 100 by 100 mm physical scan](../web/project_handbook/public/project/crtouch-two-object-100x100.png)

The plot shows physical samples only: colored circles are contact measurements
and red crosses are no-contact measurements. Empty regions of the authorized
100 × 100 mm field were not silently converted into measured pixels.

### Files retained for software analysis

- Raw physical CSV:
  `data/crtouch_profiles/two_object_100x100_20260728_185040.csv`
- Plot:
  `data/crtouch_profiles/two_object_100x100_20260728_185040.png`
- Machine-readable summary:
  `data/crtouch_profiles/two_object_100x100_20260728_185040_summary.json`
- Reusable real-hardware runner:
  `tools/run_two_object_adaptive_scan.py`
- Discovery configuration:
  `config/two_object_discovery.json`

### Engineering conclusion

The feedback loop successfully found the second object, preserved the empty
gap, resolved different object heights, and concentrated measurements around
both boundaries. The result validates adaptive coarse-contact discovery. It
does not establish micron-scale metrology: XY boundary accuracy is limited by
the 0.5 mm refinement pitch, and Z is quantized by the 0.05 mm command step.

### Repeating this scan from SPM Operator

The validated workflow is integrated into the desktop software:

1. Start **SPM Operator** and connect the MK4S.
2. Select **OPERATIONAL** motion authorization.
3. Fix both spacers, confirm the Y105 discovery path is clear, and keep hands
   outside the machine.
4. Click **Repeat Two-Object Scan** in the main header, or select
   **Tools → Repeat Validated Two-Object Scan…**.
5. Review the locked field, speed, Z increment, hard floor, and retract height.
6. Select **Authorize and Start Real Scan**.
7. Follow physical-point progress in Scan Control. The software shows component
   discovery and cooling checkpoints in the live log.
8. At completion, open the retained plot or handbook from the result dialog.

The repeat command cannot start while another worker is active, while the MK4S
is disconnected, without OPERATIONAL authorization, or when the dual-USB/Mega
readiness gate reports a blocker. Protocol geometry and Z safety values are
locked to the validated run rather than exposed as casual editable controls.

## 12. Mechanical crash and mandatory lockout

**Date:** 28 July 2026  
**Status:** LOCKOUT CLEARED 29 JULY 2026 AFTER INSPECTION AND MONITORED LIMIT VERIFICATION

A reachable-area survey incorrectly interpreted the CR Touch/nozzle separation
and end clearances as a signed probe-coordinate offset.
The resulting envelope was unsafe and the CR Touch collided. The operator
stopped the scan and pressed reset.

No result from that interrupted reachable-area survey is approved for limits,
calibration, or normal scanning. Viewed from the front, the CR Touch is mounted
on the nozzle's right side with approximately 51 mm pin-to-pin separation. The
current conservative end rule is asymmetric:

- in the leftmost 55 mm, carriage movement may be possible but CR Touch
  measurement is unavailable;
- in the rightmost 55 mm, carriage movement is prohibited because the
  right-mounted CR Touch can exceed the safe boundary and collide.

The software lockout file is
`config/crtouch_hardware_lockout.json`. Real Measurement must remain disabled
until an unpowered physical inspection is completed and the operator explicitly
confirms the CR Touch housing, pin, mount, wiring, nozzle, and carriage condition.

### Post-inspection coordinate-control rule

After visual inspection, low-speed relative motion checks established the
operator convention documented in the main handbook. All future motion is
specified as the CR Touch measurement point moving across the sample:

- right `+X`, left `-X`;
- front/toward operator `+Y`, back/away from operator `-Y`;
- up `+Z`, down `-Z`;
- Probe Out and Probe In.

The Y stage physically moves opposite to the requested CR Touch measurement
direction. Software must perform that translation internally and display the
machine action separately. The current right-side position is a safety limit;
no CR Touch `+X/right` test is permitted from that position.

## 13. Full verified-envelope two-magnet discovery

**Date:** 29 July 2026  
**Result:** PASS

After the inspection, each travel direction was exercised under direct operator
observation. The resulting native scan envelope is X −150 to 0 mm and Y 0 to
195 mm. A fresh bare-stage CR Touch approach established local trigger Z = 0
and safe XY travel Z = 15 mm. These are post-reset local coordinates, not a
substitute for future machine homing and metrology calibration.

The fast workflow used a 20 mm serpentine discovery grid over the complete
verified envelope. This pitch is small enough to intersect a nominal 29.2 mm
circle. It found two independent raised regions without being given their
locations, then concentrated 5 mm physical samples around each candidate.

![Verified-envelope two-magnet map](../web/project_handbook/public/project/crtouch-verified-two-magnet-map.png)

Results:

- 244 physical measurements
- 60 CR Touch contacts
- Magnet 1 map center: X 33.3 mm, Y 121.7 mm
- Magnet 2 map center: X 80.0 mm, Y 77.5 mm
- map frame: CR Touch left-to-right X and back-to-front Y
- final state: Z 15 mm, Probe In, scan process exited normally

Retained evidence:

- `data/crtouch_profiles/verified_two_magnet_map_20260729_171910.csv`
- `data/crtouch_profiles/verified_two_magnet_map_20260729_171910.png`
- `data/crtouch_profiles/verified_two_magnet_map_20260729_171910_summary.json`
- `tools/run_verified_two_magnet_map.py`

This is a coarse object-discovery map, not micron-resolution topography. Green
points are physical CR Touch contacts; gray crosses are physical no-contact
samples. The black circles use the known 29.2 mm nominal diameter only as a
visual overlay.

## 14. Stage 2 centered-probe commissioning

**Date:** 30 July 2026  
**Result:** PASS

The nozzle, heater, hotend thermistor and toolhead fans were removed. CR Touch
was mounted near the former nozzle centerline. This permanently invalidated the
right-side coordinates in Section 13 for current motion; they remain historical
evidence only.

The commissioning sequence verified:

1. stock Buddy 6.2.4+8909 communication and zero heater targets/outputs;
2. Mega firmware 0.8.5, D3 LOW/unlatched and D8 high impedance;
3. five visible Probe Out/In cycles;
4. Z upper reference at 220.00 mm;
5. five same-point 0.05 mm approaches, all triggering at Z28.05;
6. precise X and Y homing classified as perfect by the stock firmware;
7. 15 mm measurement insets at the homed X and Y edges;
8. visual and commanded verification of all four measurement corners;
9. a five-point bare-stage contact map.

Commissioned envelope and Z evidence:

| Item | Value |
|---|---:|
| X | 15.50–250.00 mm |
| Y | 12.50–210.00 mm |
| Safe XY/retract Z | 45.00 mm |
| Mean bare-stage trigger | 28.11 mm |
| Bare-stage minimum/maximum | 27.80 / 28.40 mm |
| Stage-map peak-to-peak | 0.60 mm |

The five identical same-point results demonstrate repeatability within the
50 µm commanded step; they do not prove 50 µm absolute accuracy. The 0.60 mm
field variation includes stage tilt/flatness and system effects. Profiling
software must retain raw trigger Z and apply a separately visible background
plane or calibrated stage map rather than presenting uncompensated height as
sample corrugation.

Retained evidence:

- `data/crtouch_profiles/stage2_centered_commissioning_20260730.csv`
- `data/crtouch_profiles/stage2_centered_commissioning_20260730.json`
- `config/crtouch_mount_profiles.json`
- `config/crtouch_hardware_lockout.json`
