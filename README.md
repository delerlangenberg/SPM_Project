# SPM_Project

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

**Modular Control and Scanning System for Scanning Probe Microscopy**

A research-grade, extensible Python application for SPM control combining hardware abstraction, scan pattern generation, real-time visualization, and AI-based processing.

---

## 🔬 Overview

SPM_Project provides a complete control system for Scanning Probe Microscopes (SPM) including:

- 🎯 **Multiple Scan Modes**: STM, AFM (contact & non-contact), profiling
- 🎮 **Hardware Abstraction**: Simulated and real hardware support
- 📊 **Real-time Visualization**: Live plots and data display
- 🤖 **AI Integration**: Pattern matching and automated analysis
- 🔧 **Modular Architecture**: Easy to extend and customize
- 🖨️ **Motion Platform**: Uses Prusa MK4S 3D printer for XY positioning

---

## ✨ Key Features

### Modular Architecture

```
┌─────────────────────────────────────────────────────┐
│                  User Interface (PyQt5)             │
├─────────────────────────────────────────────────────┤
│              Scanning Engine & Modes                │
├─────────────────────────────────────────────────────┤
│         Hardware Abstraction Layer (ABC)            │
├─────────────────────────────────────────────────────┤
│    Motion Backend    │    Z-Control    │  Sensors   │
├─────────────────────────────────────────────────────┤
│         Prusa MK4S   │   Arduino       │  ADC/DAC   │
└─────────────────────────────────────────────────────┘
```

### Scan Modes

- **STM Mode**: Scanning Tunneling Microscopy
- **AFM Contact**: Atomic Force Microscopy (contact mode)
- **AFM Non-Contact**: Dynamic AFM operation
- **Profiling Mode**: Single-line scans and cross-sections

### Hardware Support

- **Simulated Hardware**: Full simulation for development and testing
- **Prusa MK4S Integration**: Uses 3D printer for precise XY motion
- **Arduino Z-Control**: Real-time feedback for tip-sample distance
- **Extensible**: Easy to add new hardware backends

---

## 📦 Installation

### Prerequisites

- Python 3.10 or higher
- PyQt5-compatible system (Linux, macOS, Windows)
- Optional: Prusa MK4S 3D printer for motion control
- Optional: Arduino for Z-axis control

### Quick Install

```bash
# Clone the repository
git clone https://github.com/yourusername/SPM_Project.git
cd SPM_Project

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Or install as package
pip install -e .
```

### Development Install

```bash
# Install with development tools
pip install -e ".[dev]"
```

---

## 🚀 Quick Start

### Running the Application

```bash
# Run from module
python -m SPM_Project.main

# Or if installed as package
spm
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=SPM_Project tests/

# Run specific test file
pytest tests/test_scan.py
```

### Using Simulation Mode

The application starts in simulation mode by default - no hardware required!

1. Launch the application
2. Select a scan mode (STM, AFM, etc.)
3. Configure scan parameters
4. Click "Start Scan"
5. Watch real-time visualization

---

## 📚 Documentation

- [Project Overview](docs/PROJECT_OVERVIEW.md) - Architecture and design
- [Roadmap](docs/ROADMAP.md) - Development plan and milestones
- [Contributing](CONTRIBUTING.md) - How to contribute

---

## 🏗️ Project Structure

```
SPM_Project/
├── core/                  # Core scanning and control logic
│   ├── scan/             # Scan modes and patterns
│   ├── motion/           # Motion control
│   ├── system/           # System management
│   └── z_control/        # Z-axis control
├── hardware/             # Hardware interfaces
│   ├── motor/            # Motor controllers
│   └── z_control/        # Z-hardware drivers
├── interface/            # PyQt5 GUI
│   ├── layout/           # Main window layout
│   ├── panels/           # UI panels
│   └── helpers/          # UI utilities
├── simulation/           # Hardware simulators
├── processing/           # Data processing
│   └── pattern_matching/ # AI/ML processing
├── ai/                   # AI models and utilities
├── tests/                # Test suite
├── tools/                # Development utilities
└── docs/                 # Documentation
```

---

## 🎯 Usage Examples

### Performing a Scan

```python
from SPM_Project.core.scan.modes import STMMode
from SPM_Project.simulation.mock_motor_driver import MockMotorDriver

# Create hardware (simulated)
motor = MockMotorDriver()
z_control = MockZController()

# Create scan mode
stm = STMMode(motor, z_control)

# Configure scan
params = {
    'width': 100,   # nm
    'height': 100,  # nm
    'points': 128,  # resolution
}

# Execute scan
stm.prepare(params)
data = stm.execute()
stm.finalize()
```

### Adding a Custom Scan Mode

```python
from SPM_Project.core.scan.modes import BaseScanMode

class MyCustomMode(BaseScanMode):
    def prepare(self):
        # Initialize hardware
        pass
    
    def execute(self):
        # Perform scan
        return scan_data
    
    def finalize(self):
        # Cleanup
        pass
```

---

## 🔧 Configuration

### Hardware Configuration

Edit hardware configuration in your launch script:

```python
config = {
    'motion': {
        'type': 'prusa',  # or 'simulated'
        'port': '/dev/ttyUSB0',
        'baudrate': 115200,
    },
    'z_control': {
        'type': 'arduino',  # or 'simulated'
        'port': '/dev/ttyACM0',
    }
}
```

### Scan Parameters

Configure scan parameters through the UI or programmatically:

- Scan area (width, height)
- Resolution (points per line)
- Scan speed
- Z-feedback parameters
- Data acquisition settings

---

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for:

- Code style guidelines  
- Architecture principles
- Testing requirements
- Pull request process

### Current Priority Areas

1. ✅ Prusa MK4S motion backend integration
2. 📝 Documentation improvements
3. 🧪 Test coverage expansion
4. 🐛 Bug fixes and stability

---

## 🗺️ Roadmap

See [ROADMAP.md](docs/ROADMAP.md) for detailed development plans.

**Current Phase**: Motion Platform Integration (Prusa MK4S)  
**Next Release**: v0.1.0 with full simulation and Prusa integration

---

## 🐛 Known Issues

- Prusa motion backend not yet implemented (in progress)
- Some hardware control panels are placeholders
- Limited documentation for advanced features

See [Issues](https://github.com/yourusername/SPM_Project/issues) for complete list.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👤 Author

**Dr. Deler Langenberg**

---

## 🙏 Acknowledgments

- Built with PyQt5 for the GUI framework
- pyqtgraph for real-time visualization
- pytest for testing infrastructure
- NumPy for numerical computations

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/SPM_Project/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/SPM_Project/discussions)

---

**Status**: Active Development | Version 0.1.0-dev | Last Updated: 2026-02-15
