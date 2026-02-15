# Contributing to SPM_Project

Thank you for your interest in contributing to the SPM Control System! This document provides guidelines for contributing to the project.

## 🎯 Project Goals

This project aims to provide a **modular, research-grade control system** for Scanning Probe Microscopy with:
- Clean separation of concerns across layers
- Hardware abstraction (simulated and real devices)
- Extensible scan modes and processing pipelines
- Professional code quality

## 📋 Code of Conduct

- Be respectful and constructive
- Focus on improving the codebase
- Document your changes clearly
- Write tests for new features

## 🏗️ Architecture Principles

Our architecture follows these key principles:

### 1. **Layered Architecture**
```
UI Layer → Scanning Engine → Hardware Abstraction → Physical Hardware
```

Each layer should only communicate with adjacent layers through well-defined interfaces.

### 2. **Dependency Injection**
Use constructor injection for dependencies. Avoid global state.

```python
class ScanMode:
    def __init__(self, motion_driver, z_controller):
        self.motion = motion_driver
        self.z_control = z_controller
```

### 3. **Abstract Base Classes**
All hardware-facing components must implement abstract interfaces:

```python
from abc import ABC, abstractmethod

class MotionDriver(ABC):
    @abstractmethod
    def move_to(self, x, y):
        pass
```

## 📝 Coding Standards

### Naming Conventions

- **Classes**: `PascalCase`
  ```python
  class ScanPatternSimulator:
  ```

- **Functions/Methods**: `snake_case`
  ```python
  def execute_scan(self):
  ```

- **Constants**: `UPPER_SNAKE_CASE`
  ```python
  MAX_SCAN_SIZE = 1000
  ```

- **Private members**: Prefix with `_`
  ```python
  def _internal_helper(self):
  ```

### Import Style

**Always use absolute imports:**
```python
# Good
from SPM_Project.core.scan.modes import BaseScanMode

# Bad
from ..core.scan.modes import BaseScanMode
```

### Docstrings

Use Google-style docstrings for all public functions and classes:

```python
def execute_scan(self, pattern, parameters):
    """Execute a scan with the given pattern.
    
    Args:
        pattern (str): The scan pattern type (raster, spiral, etc.)
        parameters (dict): Pattern-specific parameters
        
    Returns:
        ndarray: The acquired scan data
        
    Raises:
        ValueError: If pattern is not recognized
    """
    pass
```

### Type Hints

Use type hints where helpful (especially for public APIs):

```python
def move_to(self, x: float, y: float) -> bool:
    """Move to the specified position."""
    pass
```

## 🧪 Testing

### Writing Tests

- Place tests in `tests/` directory
- Name test files `test_<module>.py`
- Name test classes `Test<ClassName>`
- Name test functions `test_<behavior>`

```python
# tests/test_scan_mode.py
class TestBaseScanMode:
    def test_initialization_with_valid_parameters(self):
        """Test that scan mode initializes correctly."""
        mode = BaseScanMode(valid_params)
        assert mode.is_ready()
    
    def test_execute_raises_error_when_not_prepared(self):
        """Test that execute raises error if prepare not called."""
        mode = BaseScanMode(params)
        with pytest.raises(RuntimeError):
            mode.execute()
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_scan_mode.py

# Run with coverage
pytest --cov=SPM_Project tests/
```

## 🔀 Git Workflow

### Branch Naming

- `feature/description` - New features
- `fix/description` - Bug fixes
- `docs/description` - Documentation updates
- `refactor/description` - Code refactoring

### Commit Messages

Follow conventional commit format:

```
type(scope): Brief description

Detailed explanation if needed.

- Additional point 1
- Additional point 2
```

Types: `feat`, `fix`, `docs`, `test`, `refactor`, `chore`

Examples:
```
feat(scan): Add spiral scan pattern mode

Implement new spiral scan pattern for faster acquisition
of small features.

- Add SpiralScanPattern class
- Update pattern selector in UI
- Add corresponding tests
```

```
fix(z-control): Correct feedback loop instability

The PID controller was oscillating due to incorrect
gain calculation. Fixed by normalizing the derivative term.
```

## 📦 Adding New Features

### Adding a New Scan Mode

1. Create a new class in `core/scan/modes/`
2. Inherit from `BaseScanMode`
3. Implement required methods: `prepare()`, `execute()`, `finalize()`
4. Add tests in `tests/`
5. Register in UI's mode selector

### Adding Hardware Support

1. Create abstract interface in `hardware/`
2. Implement simulator in `simulation/`
3. Implement real driver (if hardware available)
4. Add factory pattern for selection
5. Write integration tests

### Adding Processing Pipeline

1. Create new module in `processing/`
2. Define clear input/output contracts
3. Keep processing independent from acquisition
4. Add configuration options
5. Document usage in docstrings

## 🐛 Reporting Issues

When reporting bugs, include:

- **Description**: Clear summary of the issue
- **Steps to reproduce**: Minimal example
- **Expected behavior**: What should happen
- **Actual behavior**: What actually happens
- **Environment**: OS, Python version, dependencies
- **Logs**: Relevant error messages or stack traces

## 💡 Feature Requests

For new features, describe:

- **Use case**: Why is this needed?
- **Proposed solution**: How should it work?
- **Alternatives**: Other approaches considered?
- **Impact**: What parts of the codebase are affected?

## 📚 Documentation

- Update README.md for user-facing changes
- Update PROJECT_OVERVIEW.md for architecture changes
- Add inline comments for complex logic
- Keep docstrings up to date
- Update ROADMAP.md if changing project direction

## ✅ Pull Request Checklist

Before submitting a PR:

- [ ] Code follows style guidelines
- [ ] All tests pass
- [ ] New tests added for new features
- [ ] Documentation updated
- [ ] Commit messages are clear
- [ ] No unnecessary files included
- [ ] Changes are focused and atomic

## 🔍 Code Review Process

1. Submit PR with clear description
2. Maintainer reviews within 1-2 days
3. Address feedback and update
4. Approval required before merge
5. Squash commits if needed

## 🙏 Questions?

If you have questions about contributing:

- Check existing documentation
- Look at similar implementations in the codebase
- Ask in the issue tracker

---

**Thank you for contributing to SPM_Project!**

Your efforts help make this project better for everyone.
