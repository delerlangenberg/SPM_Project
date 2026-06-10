# SPM User-Centered Interface Requirements

## 1. Purpose

This document defines the user-centered interface requirements for the SPM workstation prototype.

The goal is to make the interface:

- safe by default
- understandable for beginner operators
- useful for research operators
- clear about hardware state
- structured around real SPM concepts
- ready for future sensor and feedback integration

This document is project-specific. It does not describe a full commercial SPM product yet. It describes the current safe educational and research workstation prototype.

---

## 2. Primary Operator Personas

### Persona 1: Student Beginner

The student beginner is learning how SPM-style scanning works. They may not understand the difference between dry-run, simulated scan, Z approach, real hardware motion, and raster output.

Needs:

- clear labels
- safe defaults
- disabled dangerous actions unless explicitly enabled
- visible status messages
- strong warnings before hardware motion
- simple dry-run workflow
- readable operator log

Risks:

- may click buttons experimentally
- may confuse dry-run scan with real hardware scan
- may not understand Z movement risk
- may not know whether the system is connected or safe

Interface implication:

- dry-run must remain the default
- real hardware actions must be visually separated
- real hardware actions must require explicit arming and confirmation
- terminology must be beginner-readable

---

### Persona 2: Research Operator

The research operator uses the workstation to prepare, repeat, and inspect scan profiles. They need reproducibility, clear status, output files, and predictable behavior.

Needs:

- scan area control
- resolution control
- Z height control
- output file visibility
- color map selection
- generated raster preview
- logs of executed actions
- reliable validation before execution

Risks:

- may run repeated scans quickly
- may assume old hardware state is still valid
- may need to distinguish profile validation from execution

Interface implication:

- validation state should be visible
- generated output should be visible
- scan parameters should be grouped logically
- execution should be separated into dry-run and real hardware paths

---

### Persona 3: Developer / Hardware Maintainer

The developer or hardware maintainer tests hardware connection, safety logic, driver behavior, and future sensor integration.

Needs:

- hardware connection status
- port and baudrate visibility
- dry-run Z control
- diagnostics
- operator log
- testable safety states
- predictable state transitions

Risks:

- may bypass GUI assumptions during testing
- may need to identify whether a problem is GUI, CLI, driver, or hardware related

Interface implication:

- hardware/system panel must expose state clearly
- safety panel must show armed/disarmed state
- logs must separate scan, Z, hardware, and safety events
- tests must lock critical safety behavior

---

## 3. Hardware and Software Components

### Current Hardware-Related Components

- XY scan backend through configured scan execution path
- Prusa-based motion backend for verified educational raster scan
- configured hardware port, currently COM5 in tested setup
- Z scanner dry-run driver
- future real Z scanner / actuator
- future SPM sensor signal channel

### Current Software Components

- PyQt GUI launcher
- CLI scan launcher
- scan profile validation
- dry-run scan mode
- hardware scan mode
- raster plot generation
- Z dry-run control panel
- operator log
- automated tests
- project backups and Git milestones

### Current Feedback Channels

- GUI status labels
- operator log
- confirmation popups
- validation output
- generated CSV file
- generated raster PNG
- automated test results

### Future Feedback Channels

- live raster preview
- real sensor signal display
- live Z feedback
- hardware readiness indicator
- emergency/interlock state
- connected/disconnected machine state

---

## 4. Safety Assumptions

The project must remain safe by default.

Current safety assumptions:

- dry-run scan is the default safe mode
- Z controls are dry-run only at the current stage
- hardware scan is possible but must be visually separated
- hardware execution requires confirmation
- generated output files must be restored before milestone commits
- no hidden hardware movement should occur from validation or dry-run actions

Required next safety improvement:

- hardware execution must start DISARMED
- REAL HARDWARE SCAN must be disabled by default
- operator must explicitly arm hardware mode
- disarming must immediately disable hardware execution
- armed state must be visible in the Hardware / System Connection panel
- operator log must record arm/disarm/cancel actions

---

## 5. Primary Workflows

### Workflow A: Safe Dry-Run Scan

1. Operator enters scan parameters.
2. Operator selects output file and color map.
3. Operator clicks Validate Profile.
4. GUI confirms validation result.
5. Operator clicks Dry Run Scan - No Hardware Movement.
6. Confirmation appears.
7. Dry-run scan executes without hardware movement.
8. CSV output is generated.
9. Raster plot is generated.
10. Operator log records the process.

This is the default beginner workflow.

---

### Workflow B: Z Dry-Run Approach and Retract

1. Operator connects Z dry-run driver.
2. Operator checks Z status.
3. Operator enters target Z and step size.
4. Operator runs Z move test, approach, or retract.
5. Confirmation appears before critical Z action.
6. Operator log records each dry-run Z event.
7. Operator disconnects Z dry-run driver.

This workflow supports future Z scanner integration without current hardware risk.

---

### Workflow C: Real Hardware Scan

1. Operator validates scan profile.
2. Operator confirms hardware/system status.
3. Operator explicitly arms hardware mode.
4. GUI enables REAL HARDWARE SCAN.
5. Operator clicks REAL HARDWARE SCAN.
6. Strong confirmation popup appears.
7. If operator cancels, no hardware movement starts.
8. If operator confirms, hardware scan executes.
9. Hardware scan output is logged and plotted.
10. Operator disarms hardware mode after use.

This workflow must be protected by state, color, layout, confirmation, and tests.

---

### Workflow D: Invalid Input Recovery

1. Operator enters invalid scan values.
2. Operator clicks Validate Profile or execution button.
3. GUI rejects the profile.
4. Operator log explains the issue.
5. No scan or hardware action starts.
6. Operator corrects parameters and validates again.

This workflow must be beginner-readable and error-tolerant.

---

### Workflow E: Output Review

1. Operator completes dry-run or hardware scan.
2. GUI generates CSV output.
3. GUI generates raster PNG.
4. Operator checks output location.
5. Future interface displays image in Live Data / Raster Plot Preview.

---

## 6. Interface Structure

The current workstation interface structure is:

### Top

- System status

### Left

- XY Scan Setup
- Scan Execution

### Center

- Live Data / Raster Plot Preview

### Right

- Z Scanner / Height Control
- Hardware / System Connection
- Global Safety / Status

### Bottom

- Operator Log

Design rule:

Each panel must match a real SPM concept.

- XY parameters belong in XY Scan Setup.
- Z height, approach, and retract belong in Z Scanner / Height Control.
- real hardware execution belongs in Hardware / System Connection.
- arming, confirmations, and safety state belong in Global Safety / Status.
- output preview belongs in Live Data / Raster Plot Preview.
- events and diagnostics belong in Operator Log.

---

## 7. Functional Requirements

### Scan Profile

- GUI shall allow entry of X minimum and maximum.
- GUI shall allow entry of Y minimum and maximum.
- GUI shall allow entry of scan Z height.
- GUI shall allow entry of X and Y resolution.
- GUI shall validate scan profile before execution.
- GUI shall show validation result in the operator log.

### Dry-Run Scan

- GUI shall provide Dry Run Scan - No Hardware Movement.
- Dry-run scan shall not move real hardware.
- Dry-run scan shall generate CSV output.
- Dry-run scan shall generate raster plot output.
- Dry-run scan shall log the selected color map.

### Hardware Scan

- GUI shall visually separate hardware scan from dry-run scan.
- GUI shall label real hardware execution clearly.
- GUI shall require critical confirmation before hardware execution.
- GUI shall log hardware scan cancellation.
- GUI shall support future armed/disarmed safety state.

### Z Scanner / Height Control

- GUI shall provide Z dry-run connection controls.
- GUI shall provide Z move test.
- GUI shall provide Z approach.
- GUI shall provide Z retract.
- GUI shall show Z status after each action.
- GUI shall confirm critical Z actions.

### Hardware / System Connection

- GUI shall show hardware/system connection status.
- GUI shall contain real hardware scan controls.
- GUI shall later expose port, baudrate, readiness, and last known state.

### Global Safety / Status

- GUI shall show safety state.
- GUI shall later show hardware armed/disarmed state.
- GUI shall later show safe scan limits and safe Z range.
- GUI shall log safety-related events.

### Data / Plot Area

- GUI shall reserve central space for raster preview.
- GUI shall later display last generated raster PNG.
- GUI shall later support live signal or raster feedback.

---

## 8. Non-Functional Requirements

### Safety

- dangerous actions shall be disabled or separated by default.
- hardware execution shall never be hidden inside ordinary scan controls.
- critical actions shall require confirmation.
- dry-run shall remain the default safe mode.

### Usability

- labels shall be beginner-readable.
- panels shall follow SPM concepts.
- frequent actions shall be easy to find.
- dangerous actions shall be visually distinct.

### Responsiveness

- GUI shall remain responsive during validation.
- scan execution output shall be logged clearly.
- future long-running operations should avoid freezing the interface.

### Error Tolerance

- invalid profiles shall be rejected before execution.
- cancellation shall be safe and logged.
- operator mistakes shall not silently trigger hardware movement.

### Maintainability

- safety behavior shall be covered by automated tests.
- each milestone shall be backed up and committed.
- generated runtime files shall not be committed accidentally.

### Accessibility: Future Requirement

Later versions should consider:

- high-contrast mode
- keyboard navigation
- tooltips
- screen-reader-compatible labels
- language options

These are not required for the current prototype phase.

---

## 9. Project-Specific Design Principles

The SPM workstation interface shall follow these principles:

1. Safe by default.
2. Dry-run before hardware.
3. Hardware state must be visible.
4. Critical actions must be confirmed.
5. XY, Z, hardware, safety, data, and logs must be separated.
6. Beginner operators must understand what each button does.
7. The interface should map directly to the physical machine.
8. Tests must protect safety-critical behavior.
9. Each phase must end with validation, backup, and commit.
10. Future features should extend the structure, not break it.

---

## 10. Next Implementation Phases

### Phase 6.3B: Hardware Armed / Disarmed State

Planned behavior:

- hardware mode starts DISARMED
- REAL HARDWARE SCAN button disabled by default
- add ARM HARDWARE button
- add DISARM HARDWARE button
- hardware status label shows HARDWARE DISARMED or HARDWARE ARMED
- arming and disarming are logged
- hardware scan cannot run unless armed
- tests confirm state behavior

### Phase 6.4: Better Status Labels and Color States

Planned behavior:

- green for ready/safe
- red for active/dangerous hardware state
- grey for disabled/unavailable
- orange/yellow for warning/caution

### Phase 6.5: Beginner Guidance and Tooltips

Planned behavior:

- add tooltips to key controls
- add short explanation labels for dry-run, hardware scan, Z approach, and output preview
- improve terminology consistency

### Phase 7: Raster Preview Integration

Planned behavior:

- display generated raster PNG in center panel
- update preview after dry-run and hardware scan
- show missing-output state clearly

### Phase 8: Real Feedback and Sensor Integration Planning

Planned behavior:

- define future sensor signal channel
- define future Z feedback display
- define synchronization requirements
- prepare for real SPM integration
