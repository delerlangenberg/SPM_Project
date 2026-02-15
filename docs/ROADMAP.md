# SPM_Project Roadmap

This document outlines the development roadmap for the SPM Control System.

## Project Status

**Current Phase**: Foundation & Simulation ✅  
**Next Phase**: Hardware Integration 🔄

---

## ✅ Completed

### Phase 1: Core Architecture (Completed)

- [x] Define layered architecture
- [x] Establish coding conventions
- [x] Set up project structure
- [x] Create abstract base classes for hardware
- [x] Implement dependency injection pattern

### Phase 2: Scanning Engine (Completed)

- [x] BaseScanMode template implementation
- [x] STM mode implementation
- [x] AFM contact mode
- [x] AFM non-contact mode
- [x] Profiling mode
- [x] Scan pattern generators

### Phase 3: Simulation Layer (Completed)

- [x] Mock motor drivers
- [x] Virtual Z-control simulation
- [x] Surface model simulator
- [x] Tip-sample interaction simulator
- [x] Scan pattern visualization
- [x] Z-feedback simulation

### Phase 4: User Interface (Completed)

- [x] Main window with dock system
- [x] Scan control panel
- [x] Live visualization area
- [x] Status bar with indicators
- [x] Menu bar with actions
- [x] Hardware diagnostics panel

### Phase 5: Testing Infrastructure (Completed)

- [x] Pytest configuration
- [x] Test suite for scan modes
- [x] Test suite for UI components
- [x] Test coverage for hardware abstraction
- [x] Test utilities and fixtures

---

## 🔄 In Progress

### Phase 6: Motion Platform Integration (Current)

**Goal**: Integrate Prusa MK4S 3D printer as motion platform

- [ ] Design MotionBackend interface
  - [ ] Define move commands API
  - [ ] Define state reporting API
  - [ ] Define homing and calibration API
  - [ ] Error handling strategy

- [ ] Implement PrusaGcodeBackend
  - [ ] G-code command generation
  - [ ] Serial/USB communication
  - [ ] Command queue management
  - [ ] Position tracking
  - [ ] Safety limits enforcement

- [ ] Integration Testing
  - [ ] Test connection establishment
  - [ ] Test basic movement commands
  - [ ] Test coordinate transformation
  - [ ] Test error recovery
  - [ ] Verify position accuracy

- [ ] UI Integration
  - [ ] Add Prusa backend to hardware selector
  - [ ] Show connection status
  - [ ] Display current position
  - [ ] Jog controls for manual movement

**Target**: End of Q1 2026

---

## 📋 Planned

### Phase 7: Z-Control Hardware (Q2 2026)

- [ ] Arduino interface implementation
- [ ] ADC reading for sensor input
- [ ] DAC/PWM output for Z-actuator
- [ ] Real-time feedback loop
- [ ] Safety limits and emergency stop
- [ ] Calibration procedures

### Phase 8: Data Acquisition (Q2 2026)

- [ ] Real-time data streaming
- [ ] Buffering and storage
- [ ] File format support (HDF5, custom binary)
- [ ] Metadata recording
- [ ] Data compression options

### Phase 9: Processing Pipeline (Q3 2026)

- [ ] Line-by-line processing
- [ ] Plane fitting and leveling
- [ ] Noise filtering
- [ ] Feature detection
- [ ] Image export (PNG, TIFF)

### Phase 10: AI/ML Integration (Q3-Q4 2026)

- [ ] Pattern matching for tip approach
- [ ] Surface feature classification
- [ ] Automated parameter tuning
- [ ] Drift compensation
- [ ] Event detection

### Phase 11: Advanced Features (Q4 2026)

- [ ] Spectroscopy modes
- [ ] Multi-pass scanning
- [ ] Lithography mode
- [ ] Force curve acquisition
- [ ] Real-time FFT analysis

### Phase 12: Documentation & Polish (Q4 2026)

- [ ] User manual
- [ ] API documentation (Sphinx)
- [ ] Tutorial videos
- [ ] Example datasets
- [ ] Installation guide for different platforms

---

## 🎯 Long-term Vision

### Phase 13: Network/Remote Operation (2027)

- [ ] Web-based monitoring interface
- [ ] Remote control capabilities
- [ ] Multi-user access control
- [ ] Cloud data storage integration

### Phase 14: Advanced Hardware Support (2027)

- [ ] Support for commercial SPM controllers
- [ ] Multi-channel data acquisition
- [ ] Environmental control integration (temperature, humidity)
- [ ] Vibration monitoring

### Phase 15: Collaboration Features (2027+)

- [ ] Shared measurement protocols
- [ ] Data sharing and collaboration
- [ ] Instrument booking system
- [ ] Automated experiment scheduling

---

## 🚧 Technical Debt & Improvements

### Code Quality

- [ ] Add more comprehensive error handling
- [ ] Improve logging throughout application
- [ ] Add configuration file support (YAML/JSON)
- [ ] Refactor large functions into smaller units
- [ ] Add more docstrings and comments

### Performance

- [ ] Profile real-time scanning performance
- [ ] Optimize data streaming
- [ ] Reduce UI update overhead
- [ ] Multithreading for long operations

### Testing

- [ ] Increase test coverage to >80%
- [ ] Add integration tests
- [ ] Add performance benchmarks
- [ ] Add regression tests for critical paths

### Documentation

- [ ] Complete all TODO items in code
- [ ] Add architecture diagrams
- [ ] Document all configuration options
- [ ] Create troubleshooting guide

---

## 💡 Feature Ideas (Backlog)

These are potential features for future consideration:

- **Multi-tip scanning**: Support for parallel probe operation
- **Machine learning autofocus**: AI-assisted tip approach
- **VR visualization**: 3D surface rendering in VR
- **Script recorder**: Record and replay measurement sequences
- **Plugin system**: Allow third-party extensions
- **Mobile app**: Monitor scans from smartphone
- **Custom scan patterns**: User-defined scan trajectories
- **Real-time collaboration**: Multiple users observing same scan
- **Automated tip exchange**: Robotic tip changing system

---

## 📊 Metrics & Success Criteria

### Phase 6 Success Criteria

- [ ] Successfully move Prusa to any XY position within workspace
- [ ] Position accuracy within ±10 µm
- [ ] Movement reproducibility within ±5 µm
- [ ] Safe operation with emergency stop functional
- [ ] Connection/disconnection stable and reliable

### Overall Project Goals

- **Reliability**: 99% uptime during scanning operations
- **Performance**: Real-time scanning at >10 Hz for 100x100 grid
- **Usability**: New users can perform basic scan within 30 minutes
- **Maintainability**: New scan mode can be added in <2 hours
- **Extensibility**: Hardware backend can be swapped without UI changes

---

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on contributing to any of these phases.

Priority areas for contributions:
1. **Motion platform integration** (current phase)
2. **Documentation improvements**
3. **Test coverage expansion**
4. **Bug fixes and stability**

---

## 📅 Release Schedule

- **v0.1.0** (Q1 2026): Simulation complete, Prusa integration
- **v0.2.0** (Q2 2026): Z-control hardware, basic scanning
- **v0.3.0** (Q3 2026): Processing pipeline, AI features
- **v1.0.0** (Q4 2026): First stable release with full feature set

---

**Last Updated**: 2026-02-15  
**Current Version**: 0.1.0-dev  
**Next Milestone**: Prusa MK4S motion backend integration
