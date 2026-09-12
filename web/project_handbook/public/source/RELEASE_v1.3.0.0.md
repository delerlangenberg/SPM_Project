# SPM Operator v1.3.0.0

**Release date:** 30 July 2026  
**Profile:** `center_crtouch_nozzle_removed`

## Stage 2 result

The nozzle, hotend heater, hotend thermistor and toolhead fans have been
removed. CR Touch is mounted near the former nozzle centerline and remains
controlled by the Arduino Mega 2560 through D3/D8.

Commissioned geometry:

| Item | Verified value |
|---|---:|
| X measurement range | 15.50–250.00 mm |
| Y measurement range | 12.50–210.00 mm |
| Usable field | 234.50 × 197.50 mm |
| Usable area | 46,313.75 mm² |
| Safe XY/retract height | Z45.00 mm |
| Z upper reference | Z220.00 mm |
| Mean bare-stage trigger | Z28.11 mm |
| Five-point stage variation | 0.60 mm peak-to-peak |

Five same-point 0.05 mm approaches all triggered at Z28.05. This demonstrates
repeatability within the commanded 50 µm increment; it is not a claim of
absolute 50 µm metrology.

## Firmware policy

The installed stock Prusa-Firmware-Buddy 6.2.4+8909 is retained. It completed
X/Y precise homing and bounded XYZ scanner motion while the removed hotend
input remained open and all heater outputs remained zero.

SPM Operator applies a scanner command firewall:

- allows read-only status, bounded XYZ movement, explicit X/Y homing and
  output-off commands;
- blocks every nonzero heater target, extrusion, printing/filament workflows,
  G29, Z homing and unknown commands;
- validates the live M105 thermal state and Mega D3/D8 safe state before Real
  Measurement.

No custom xBuddy firmware was flashed and no irreversible appendix change was
performed.

## LoveBoard decision

The LoveBoard remains installed as the labelled toolhead cable breakout. Its
motor, heater, thermistor, fan, loadcell and filament-sensor sockets are
dedicated xBuddy interfaces and cannot replace the programmable Mega CR Touch
controller. Loadcell and temperature channels are reserved for separately
reviewed future experiments.

## Evidence

- `data/crtouch_profiles/stage2_centered_commissioning_20260730.json`
- `data/crtouch_profiles/stage2_centered_commissioning_20260730.csv`
- `config/crtouch_mount_profiles.json`
- `config/crtouch_hardware_lockout.json`
- `docs/STAGE2_LOVEBOARD_CONNECTOR_ASSESSMENT.md`

## Release verification

- Python regression suite: 356 passed.
- Local handbook: production build passed; 2 browser checks passed.
- Portable application: launched outside the source directory.
- Installed application: launched successfully; file, product and registry
  versions report 1.3.0.0.
- Installer:
  `installer/windows/SPM_Operator_Setup.exe`.
- Verified milestone backup:
  `D:\SPM_Prusa_Project\backups\phase_milestones\v1.3.0.0_stage2_centered_verified_20260730`.
