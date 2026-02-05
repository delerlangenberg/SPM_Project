# SPM Control System — Project Overview

## 1. Purpose

This project implements a **modular control and scanning system for a Scanning Probe Microscope (SPM)**.
It combines **hardware control, scan pattern generation, visualization, and AI-based processing** in a
single, extensible Python application.

The goal is **research-grade flexibility** rather than vendor lock-in:
hardware can be simulated or real, scan modes are pluggable, and data processing pipelines can evolve independently.

---

## 2. High-Level Architecture

The system is organized into **five core layers**, each with a clearly defined responsibility.

### 1) Hardware Abstraction Layer
- Abstract interfaces for motion, sensors, and actuators
- Supports **simulated hardware** and **real devices**
- Designed using the **Strategy pattern**

### 2) Z-Control System
- Controls probe–sample distance
- Driver factory + feedback loops
- Independent from scan geometry

### 3) Scanning Engine
- Modular scan modes (e.g. raster, line, custom)
- Uses a **Template Method** (`BaseScanMode`) to enforce workflow:
  - prepare
  - execute
  - finalize
- Scan patterns follow an **ABC-style structure** (parameterized movement logic)

### 4) User Interface (PyQt5)
- Dock-based UI layout
- Panels for:
  - scan control
  - live visualization
  - hardware state
  - diagnostics
- UI triggers scans but does **not** contain scan logic

### 5) Processing & AI Pipeline
- Post-processing of scan data
- Feature extraction, filtering, ML/AI analysis
- Decoupled from acquisition logic

---

## 3. Motion Platform Decision

The project **does not implement custom motion hardware** from scratch.

Instead, a **Prusa MK4S 3D printer** is used as the motion platform:
- Motion is controlled via **G-code commands**
- The printer is treated as a **motion backend**
- This backend conforms to the same interface as simulated hardware

This keeps the software architecture clean while leveraging a reliable, calibrated motion system.

---

## 4. Integration Flow

- UI → Scanning Engine  
- Scanning Engine → Motion Backend + Z-Control  
- Motion Backend → Physical system (or simulator)  
- Acquired Data → Visualization → Processing / AI  

Each layer communicates via **well-defined interfaces**, not direct coupling.

---

## 5. Design & Coding Conventions

- Absolute imports only
- `PascalCase` for classes
- `snake_case` for functions and variables
- Abstract base classes for all hardware-facing components
- Configuration via dictionaries, not hard-coded constants

---

## 6. Current Status

- Core architecture exists
- Simulation and scanning logic present
- Hardware abstraction in place
- **Prusa MK4S motion backend not yet implemented**

---

## 7. Next Step

Implement a **MotionBackend interface** and a first
`PrusaGcodeBackend` that can:
- connect to the printer
- send G-code move commands
- report basic state
