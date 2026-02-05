# SPM Project AI Coding Instructions

## Project Overview
This is a **Scanning Probe Microscopy (SPM) control system** built with Python and PyQt5. It provides a unified interface for hardware control (Arduino-based motors/sensors), scanning mode implementations (STM, AFM contact/non-contact), real-time visualization, and AI-assisted pattern analysis.

## Architecture Overview

### Core Layers (Bottom-Up)

**Hardware Layer** (`hardware/`)
- `arduino_link.py`: Arduino communication (currently stub)
- `adc_interface.py`: Analog-to-digital sensor readings
- `z_scanner_driver.py`: Z-axis (height) control
- `motor/`: X/Y stepper motor control

**Z-Control System** (`core/z_control/`)
- **Driver abstraction**: `z_driver_simulated.py` (testing) vs `z_driver_arduino.py` (production)
- **Factory pattern**: `z_interface.py::get_z_driver()` switches implementations based on mode
- **Feedback loop**: `z_feedback.py::ZFeedbackController` implements PID-like regulation
- **Visualization**: `z_plotter.py` for real-time height plots

**Scanning Engine** (`core/scan/`)
- **Base pattern**: `base_scan_mode.py` (ABC) defines `initialize()` → `perform_step()` → cleanup workflow
- **Concrete modes**: `modes/` subdirectory for STM, AFM-Contact, AFM-NonContact, Profiling
- **Controller**: `controller/` orchestrates scan modes with workflow management
- **Workflow**: `workflow/` contains scan job sequencing logic

**UI Layer** (`interface/`)
- **Main window** (`layout/main_window.py`): PyQt5 QMainWindow with dark theme, menu bar, dock widgets
- **Panels** (`panels/`): Modular UI components (Z-regulation, scanning, simulation, measurement)
- **Visualization** (`visualization/`): Real-time plotting with pyqtgraph

**AI/Analysis** (`ai/`)
- `pattern_matcher.py`: Pattern recognition on scan data
- `models/ml_model.py`: ML model inference
- `utils/ai_utils.py`: Helper functions for AI operations

**Data Processing** (`processing/`)
- `process_pipeline.py`: Scan data post-processing
- `preprocess.py`: Image normalization/filtering
- `pattern_matching/`: Advanced pattern analysis

**Simulation** (`simulation/`)
- Complete mock environment for testing without hardware
- `simulator_engine.py`: Core simulation orchestrator
- `scan_simulator.py`, `z_feedback_simulator.py`: Component-level simulators
- `surface_model_simulator.py`: Virtual probe environment

---

## Critical Design Patterns

### 1. **Driver Abstraction (Strategy Pattern)**
Z-drivers support two implementations:
```python
# z_interface.py
def get_z_driver(mode='simulated'):
    if mode == 'simulated':
        return SimulatedZDriver()  # Mock for testing
    elif mode == 'arduino':
        return ArduinoZDriver()    # Real hardware
```
**When modifying**: Ensure new Z-features support BOTH drivers. Add tests to `test_z_driver_simulated.py` and `test_z_driver_arduino.py`.

### 2. **Scan Mode Inheritance**
All scan types inherit from `BaseScanMode`:
```python
class STMMode(BaseScanMode):
    def initialize(self):
        """Setup Z-feedback, probe approach"""
    def perform_step(self):
        """Single X/Y pixel acquisition with Z-regulation"""
```
**When adding scan modes**: Create in `core/scan/modes/`, implement both abstract methods, add corresponding test in `tests/test_*_mode.py`.

### 3. **Configuration Dictionary Pattern**
Components accept `config` dicts for parameterization:
```python
config = {"setpoint": 5.0, "gain": 1.5, "x_range": 100}
mode = STMMode(config=config)
```
**Convention**: Config keys use snake_case, values are typed (float/int/bool). Document expected keys in docstrings.

### 4. **PyQt5 Panel Composition**
UI is built from dock widgets containing panels:
```python
# main_window.py loads:
# - ZRegulationPanel (Z feedback control)
# - SimulationPanel (mock hardware control)
# - MeasurementPanel (scanning UI)
```
**When adding UI**: Create new class in `interface/panels/`, inherit from QWidget, instantiate in MainWindow._init_dock_widgets().

---

## Developer Workflows

### Running Tests
```bash
# Run all tests
pytest

# Run specific module
pytest tests/test_z_feedback.py

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=core --cov=hardware --cov=ai
```

### Running the Application
```bash
# GUI startup
python main.py

# Or via app.py
python app.py
```

### Debugging Z-Control
- Check `core/z_control/z_interface.py::get_z_driver()` to toggle between simulated/real hardware
- Simulated driver in `core/z_control/z_driver_simulated.py` has no side effects
- Feedback loop parameters (setpoint, gain) in config dict passed to `ZFeedbackController`

### Adding New Tests
- Place in `tests/test_*.py` with pytest naming convention
- Use fixtures for Z-drivers (simulated by default) and config dicts
- Import modules with full paths: `from core.z_control.z_feedback import ZFeedbackController`

---

## Project-Specific Conventions

### Import Paths
- **Absolute imports only** (pytest.ini sets pythonpath to project root)
- Always import from package root: `from core.scan.modes.stm import STMMode`
- Never: `from ..scan.modes` (relative imports)

### Naming
- **Classes**: PascalCase (`ZFeedbackController`, `SimulatedZDriver`)
- **Functions**: snake_case (`get_z_driver`, `perform_step`, `add_data_point`)
- **Config keys**: snake_case (`z_setpoint`, `x_range`, `scan_speed`)
- **Files**: snake_case with optional prefixes (`z_driver_arduino.py`, `base_scan_mode.py`)

### Abstract Methods
- Use `@abstractmethod` in base classes (e.g., `BaseScanMode`)
- Concrete implementations provide docstrings explaining their specific behavior
- Tests verify concrete classes implement all abstract methods

### Configuration
- Pass config as dict to constructors: `STMMode(config={"setpoint": 5.0})`
- Store in `self.config` for later access
- Document required/optional keys in class docstrings

---

## Key Dependencies & Integration Points

### External Libraries
- **PyQt5**: UI framework (dark theme applied in MainWindow)
- **pyqtgraph**: Real-time plotting for Z-feedback and scan visualization
- **pytest**: Testing framework with pythonpath configured in pytest.ini
- **numpy/scipy** (assumed): Data processing in `processing/`
- **Arduino serial communication** (stub, TBD): Hardware abstraction in `hardware/arduino_link.py`

### Cross-Component Communication
1. **UI → Scan Engine**: MainWindow sends start/stop signals through panels → scan controller
2. **Scan Engine → Z-Control**: Scan modes call Z-driver (via interface factory) for height positioning
3. **Z-Feedback ↔ Scan Data**: Feedback loop regulates Z position; scan stores resulting height measurements
4. **Data → Visualization**: Scan data → processing pipeline → pyqtgraph plots
5. **AI Analysis**: Pattern matcher receives processed scan data, returns pattern classifications

### Hardware Communication (TBD)
- `hardware/arduino_link.py` is a stub; real implementation needed for motor/sensor control
- Z-drivers already abstract this; Arduino implementation in `core/z_control/z_driver_arduino.py`
- Ensure error handling for serial timeouts and connection failures

---

## Testing Approach

- **Unit tests**: Component-level (individual scan modes, Z-feedback)
- **Integration tests**: Multi-component workflows (scan mode + Z-feedback)
- **Mock hardware**: Always use `SimulatedZDriver` in tests (never real Arduino)
- **Config-driven tests**: Vary parameters via config dict fixtures
- **Example**: [test_base_scan_mode.py](../tests/test_base_scan_mode.py) validates config initialization

---

## Common Tasks

### Add a New Scan Mode
1. Create `core/scan/modes/my_mode.py` inheriting from `BaseScanMode`
2. Implement `initialize()` and `perform_step()` methods
3. Update `core/scan/modes/__init__.py` to export the class
4. Add test in `tests/test_my_mode.py` using simulated Z-driver
5. Wire into MainWindow if user-facing

### Modify Z-Feedback Regulation
1. Edit `ZFeedbackController.__init__()` and `update()` in `core/z_control/z_feedback.py`
2. Update config keys in docstring
3. Add/modify tests in `tests/test_z_feedback.py`
4. Ensure both simulated and Arduino drivers work with new parameters

### Add UI Component
1. Create class in `interface/panels/` inheriting from QWidget
2. Implement layout (QVBoxLayout, buttons, plots) in `__init__()`
3. Instantiate and add as dock widget in `MainWindow._init_dock_widgets()`
4. Create test in `tests/test_*.py` using QTest or mock components

### Debug Hardware Integration
1. Check `hardware/arduino_link.py` for serial communication issues
2. Use simulated driver first: `get_z_driver('simulated')`
3. Add debug logging before switching to real hardware
4. Verify motor control in `hardware/motor/motor_controller.py`

---

## File Navigation Quick Reference

| Task | Files |
|------|-------|
| Start here | [main.py](../main.py), [app.py](../app.py) |
| UI layout | [interface/layout/main_window.py](../interface/layout/main_window.py) |
| Scanning logic | [core/scan/base_scan_mode.py](../core/scan/base_scan_mode.py), [core/scan/modes/](../core/scan/modes/) |
| Z-control | [core/z_control/z_interface.py](../core/z_control/z_interface.py), [core/z_control/z_feedback.py](../core/z_control/z_feedback.py) |
| Testing | [pytest.ini](../pytest.ini), [tests/](../tests/) |
| Hardware stubs | [hardware/](../hardware/) |
| Simulation | [simulation/](../simulation/) |
| AI/Processing | [ai/](../ai/), [processing/](../processing/) |
