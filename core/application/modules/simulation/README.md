# Module 8: Simulation Engine

Last updated: 2026-07-15

## Purpose

Provides hardware-independent virtual SPM operation for training, demonstration, and development. The module contains no serial or PyQt imports and cannot transmit hardware commands.

## Sample types

- `half_ball`: hemispherical bump (`radius`, `height`, `center_x`, `center_y`)
- `square`: flat mesa (`width`, `height`, `edge_sharpness`, center)
- `bravais_111`: triangular lattice (`lattice_constant`, `height`, `rotation`, center)
- `bravais_100`: square lattice (same parameters)
- `bravais_110`: rectangular lattice (`lattice_constant_a`, `lattice_constant_b`, `height`, `rotation`, center)

Angles are expressed in degrees and distances in millimetres.

## Public interface

- `SimulationEngine.enable(sample_type, params)` / `disable()`
- `move_to_position(x, y, z, dt=0.05)`
- `start_scan(scan_params)` / `scan_point(...)` / `stop_scan()`
- `get_current_feedback()` / `get_topography_array(...)`
- `SampleGenerator.get_height_at_position(...)`
- `FeedbackSimulator.update(target_height, current_z, dt)`
- `ScannerController.move_to(target_x, target_y, target_z, dt)`

## Usage

```python
from core.application.modules.simulation import SimulationEngine

engine = SimulationEngine(logger)
engine.enable("half_ball", {"radius": 0.5, "height": 0.5})
feedback = engine.move_to_position(0.1, 0.2, 0.5)
```

## Configuration and artifacts

Scanner speed, acceleration, Gaussian noise, PID gains, and sample geometry are constructor/runtime parameters. The packaged `samples/` JSON files provide operator defaults. Hysteresis and noise affect only `move_to_position`; raster topography uses exact coordinates for stable training images.

## Extension guide

Add a sample name to `SAMPLE_TYPES`, implement a matching private height method in `SampleGenerator`, add a JSON preset, and extend the parameter dialog mapping and tests.

## Testing

```powershell
.\.venv\Scripts\python.exe -m pytest -q core\application\modules\simulation\tests.py
```

