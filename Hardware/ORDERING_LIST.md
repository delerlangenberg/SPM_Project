# SPM Scanner Ordering List

This document tracks parts needed to build or extend the SPM/scanner workstation.

## Ordering status labels

Use these labels:

- TODO
- SELECTED
- ORDERED
- RECEIVED
- TESTED
- INSTALLED
- REJECTED

---

## 1. Motion and scanner mechanics

| Item | Purpose | Specification | Quantity | Status | Supplier / Link | Notes |
|---|---|---|---:|---|---|---|
| XY motion platform | Raster movement or sample positioning | TBD | 1 | TODO | TBD | Check travel range, repeatability, and controller compatibility |
| Z approach actuator | Tip/sample approach | TBD | 1 | TODO | TBD | Must support safe fine movement |
| Linear guide / rail | Mechanical guidance | TBD | TBD | TODO | TBD | Low backlash preferred |
| Mounting plates | Scanner structure | TBD | TBD | TODO | TBD | Aluminium or rigid printed parts |
| Vibration isolation element | Mechanical stability | TBD | TBD | TODO | TBD | Needed before sensitive measurements |

---

## 2. Electronics and control

| Item | Purpose | Specification | Quantity | Status | Supplier / Link | Notes |
|---|---|---|---:|---|---|---|
| Arduino / microcontroller | Z-control test path | TBD | 1 | TODO | TBD | Current software uses safe dry-run Arduino driver |
| Motor driver / actuator driver | Drive Z or XY actuator | TBD | TBD | TODO | TBD | Must match actuator type |
| Power supply | Electronics power | TBD | TBD | TODO | TBD | Separate logic and motor supply if needed |
| Emergency stop switch | Safety | TBD | 1 | TODO | TBD | Required before real hardware movement |
| Limit switches | Motion safety | TBD | TBD | TODO | TBD | For X/Y/Z travel protection |
| Shielded cables | Signal and motor wiring | TBD | TBD | TODO | TBD | Reduce noise |

---

## 3. Sensor and signal chain

| Item | Purpose | Specification | Quantity | Status | Supplier / Link | Notes |
|---|---|---|---:|---|---|---|
| Probe / sensor head | Measurement signal | TBD | 1 | TODO | TBD | Depends on AFM/STM/SPM mode |
| Signal amplifier | Signal conditioning | TBD | 1 | TODO | TBD | Low noise preferred |
| Data acquisition device | Read measurement signal | TBD | 1 | TODO | TBD | Python compatibility important |
| Grounding accessories | Noise reduction | TBD | TBD | TODO | TBD | Important for stable measurements |

---

## 4. Computer and software interface

| Item | Purpose | Specification | Quantity | Status | Supplier / Link | Notes |
|---|---|---|---:|---|---|---|
| Workstation PC | Run GUI and acquisition | TBD | 1 | TODO | TBD | Windows currently used |
| USB hub / interface | Connect controllers | TBD | 1 | TODO | TBD | Industrial powered hub preferred |
| Serial adapter | COM communication | TBD | TBD | TODO | TBD | Needs stable Windows COM port |
| Monitor | Workstation display | TBD | 1 | TODO | TBD | Useful for live raster display |

---

## 5. Consumables and lab accessories

| Item | Purpose | Specification | Quantity | Status | Supplier / Link | Notes |
|---|---|---|---:|---|---|---|
| Screws / fasteners | Assembly | TBD | TBD | TODO | TBD | Keep metric sizes consistent |
| Cable labels | Wiring documentation | TBD | 1 set | TODO | TBD | Useful for debugging |
| Storage boxes | Component organization | TBD | TBD | TODO | TBD | Separate electronics and mechanics |
| Anti-static mat | Electronics handling | TBD | 1 | TODO | TBD | Recommended |
