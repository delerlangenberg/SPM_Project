# Random Two-Magnet Adaptive Discovery Test

**Date:** 31 July 2026  
**Operator setup:** two independently placed round whiteboard magnets  
**Nominal dimensions:** 29.3 mm diameter × 11.3 mm height  
**Result:** PASS

## Test purpose

Validate the complete normal workflow without supplying object coordinates:

1. scan the entire commissioned field;
2. discover separated raised-object regions;
3. estimate a center for every region;
4. narrow automatically to focused local maps;
5. preserve the physical readings, plot and safe final state.

## Wide survey

The scanner measured the full X15.50–250.00 and Y12.50–210.00 mm field at
20 mm pitch. All 143 overview points were physical measurements.

Four overview contacts formed two spatially separated components:

- component A: X75.50 at Y72.50 and Y92.50;
- component B: X175.50 and X195.50 at Y132.50.

The automatically generated seeds were X75.50/Y82.50 and X185.50/Y132.50.
The 20 mm grid is appropriate for 29.3 mm circles because its maximum
grid-cell-center distance is about 14.14 mm, below the 14.65 mm object radius.

## Focused refinement

Each seed received an independent 35 × 35 mm local scan at 5 mm pitch.
The routine collected 64 local points per object, excluding no unmeasured
interpolated points from the CSV.

| Result | Object 1 | Object 2 |
|---|---:|---:|
| Native center | X80.50/Y87.50 | X185.50/Y132.50 |
| Operator map center | X65.00/Y122.50 | X170.00/Y77.50 |
| Focused contacts | 29 | 29 |
| Contact footprint | 25 × 25 mm | 25 × 25 mm |
| Corrected mean contact height | 10.43 mm | 11.25 mm |
| Corrected observed range | 9.99–10.51 mm | 10.45–11.49 mm |

The 25 mm contact footprint is consistent with a 29.3 mm circle sampled on a
5 mm grid: the true edge lies between sampled contact and no-contact points.
The two centers are approximately 114.3 mm apart.

The height difference must not be interpreted as precision dimensional
metrology. The raised-object search uses discrete 0.5 mm Z tiers, CR Touch has
contact overtravel, and the current stage correction is a four-corner model.
Object 2 agrees closely with the nominal 11.3 mm height; Object 1 requires a
future finer local height pass if absolute height is important.

## Physical evidence

- Total measurements: 271.
- Total contacts: 62.
- Overview: 143 measurements.
- Focused maps: 128 measurements.
- CSV:
  `data/crtouch_profiles/verified_two_magnet_map_20260731_085114.csv`
- Plot:
  `data/crtouch_profiles/verified_two_magnet_map_20260731_085114.png`
- Summary:
  `data/crtouch_profiles/verified_two_magnet_map_20260731_085114_summary.json`
- Command log:
  `logs/adaptive_magnets/random_two_magnets_20260731_085113.out.log`

## Software implementation

The validated workflow is exposed in SPM Operator as **Discover & Refine
Objects**:

- **Balanced:** 20 mm overview → 5 mm focus; validated default.
- **Precision:** 20 mm overview → 2.5 mm focus.
- **Research:** 15 mm overview → 1 mm focus.

The former fixed two-cluster calculation was replaced by spatial connected
components. The normal workflow can now discover from one to 12 separated
raised-object regions. More than 12 regions fails closed rather than launching
an unexpectedly long refinement.

The physical search remains explicitly calibrated for objects approximately
9.5–12.0 mm above the mapped stage. It is not yet a general arbitrary-height
surface scanner.

## AI development boundary

A future AI planner may:

- rank discovered regions by edge uncertainty and information gain;
- choose the next local samples;
- stop refinement when confidence no longer improves;
- recommend Balanced, Precision or Research based on feature size;
- compare repeated shapes with previous scans.

It may not change the commissioned envelope, hard floor, thermal gates,
maximum object count or Probe In/Z45 fault retraction. AI output remains an
advisory sampling plan validated by deterministic safety code.

## Final state

The run completed normally at X168.00/Y150.00/Z45.00 with Probe In. The final
audit confirmed Mega READY, D3 LOW, no retained trigger latch and D8
high-impedance. M105 reported T:-20/0, B:23.93/0, @:0 and B@:0. The completed
software change passed 360 Python tests and both local-handbook browser checks.
