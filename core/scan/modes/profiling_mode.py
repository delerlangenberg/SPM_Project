# core/scan/profiling_mode.py

import numpy as np

from core.scan.base_scan_mode import BaseScanMode
from core.z_control.z_interface import get_z_driver


class ProfilingMode(BaseScanMode):
    """
    Profiling mode for 1D surface scanning along a single axis (X or Y),
    useful for quick surface height profiling at high resolution.
    """

    def __init__(self, config=None, hardware_mode=False):
      

        super().__init__(config)
        self.hardware_mode = hardware_mode
        cfg = config or {}

        self.profile_length = cfg.get("profile_length", 100)
        self.z_driver = get_z_driver(hardware_mode)
        self.axis = config.get("axis", "x")
        self.range = config.get("range", 10)
        self.resolution = config.get("resolution", 200)
        self.setpoint = config.get("setpoint", 1.0)
        self.step = self.range / self.resolution
        self.simulated_profile = None

    def initialize(self):
        print("[ProfilingMode] Initialization...")
        self.simulated_profile = self._generate_simulated_profile()
        self.position = 0
        self.data_buffer.clear()
        self.z_driver.initialize()

    def perform_step(self):
        pos = self.position
        height = self._simulate_height(pos)
        self.z_driver.set_z_position(height)
        if self.axis == "x":
            self.data_buffer.append((pos, 0, height))
        else:
            self.data_buffer.append((0, pos, height))

        pos += self.step
        if pos >= self.range:
            return "done"

        self.position = pos
        return "running"

    def finalize(self):
        print("[ProfilingMode] Finalizing scan...")
        self.z_driver.shutdown()

    def _generate_simulated_profile(self):
        x = np.linspace(0, self.range, self.resolution)
        profile = 0.5 + 0.3 * np.sin(2 * np.pi * x / self.range)
        profile += 0.05 * np.random.randn(self.resolution)  # add noise
        return profile

    def _simulate_height(self, pos):
        i = min(int((pos / self.range) * (self.resolution - 1)), self.resolution - 1)
        return self.simulated_profile[i]

# D:/Documents/Project/SPM/core/scan/profiling_mode.py

from PyQt5.QtWidgets import QDialog, QLabel, QVBoxLayout

def launch_profiler():
    """Launch a simple placeholder Profiler UI."""
    dlg = QDialog()
    dlg.setWindowTitle("Profiling Mode")
    layout = QVBoxLayout()
    layout.addWidget(QLabel("Profiler is not yet implemented."))
    dlg.setLayout(layout)
    dlg.exec_()
