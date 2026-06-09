# core/scan/stm_mode.py

import numpy as np

from core.scan.base_scan_mode import BaseScanMode
from core.z_control.z_interface import get_z_driver
from core.scan.modes import stm_mode

class StmMode(BaseScanMode):
    """
    Implements STM scanning behavior (simulated or hardware mode).
    """

    def __init__(self, config=None, hardware_mode=False):
        super().__init__(config)
        self.hardware_mode = hardware_mode
        self.z_driver = get_z_driver(hardware_mode)

        cfg = config or {}

        # Accept legacy/test config key
        self.scan_area = cfg.get("scan_area", None)

        # If scan_area is provided, use it for both axes (square scan)
        if self.scan_area is not None:
            self.x_range = self.scan_area
            self.y_range = self.scan_area
        else:
            self.x_range = cfg.get("x_range", 10)  # μm
            self.y_range = cfg.get("y_range", 10)  # μm

        self.resolution = cfg.get("resolution", 100)
        self.tunnel_current = cfg.get("setpoint", 1.0)  # nA
        self.x_step = self.x_range / self.resolution
        self.y_step = self.y_range / self.resolution
        self.simulated_surface = None










    def initialize(self):
        print("[STMMode] Initialization...")
        self.simulated_surface = self._generate_simulated_surface()
        self.current_position = (0, 0)
        self.data_buffer.clear()
        self.z_driver.initialize()

    def perform_step(self):
        x, y = self.current_position
        z = self._simulate_tunneling_signal(x, y)
        self.z_driver.set_z_position(z)

        self.data_buffer.append((x, y, z))
        x += self.x_step

        if x >= self.x_range:
            x = 0
            y += self.y_step
            if y >= self.y_range:
                return "done"

        self.current_position = (x, y)
        return "running"

    def finalize(self):
        print("[STMMode] Finalizing scan...")
        self.z_driver.shutdown()

    def _generate_simulated_surface(self):
        """
        Create a synthetic 2D topography surface.
        """
        x = np.linspace(0, self.x_range, self.resolution)
        y = np.linspace(0, self.y_range, self.resolution)
        X, Y = np.meshgrid(x, y)
        Z = 2 * np.sin(2 * np.pi * X / self.x_range) * np.cos(2 * np.pi * Y / self.y_range)
        return Z

    def _simulate_tunneling_signal(self, x, y):
        """
        Approximate the Z-height for a given (x, y) from the simulated surface.
        """
        ix = min(int((x / self.x_range) * (self.resolution - 1)), self.resolution - 1)
        iy = min(int((y / self.y_range) * (self.resolution - 1)), self.resolution - 1)
        return self.simulated_surface[iy, ix]

# D:/Documents/Project/SPM/core/scan/stm_mode.py

from PyQt5.QtWidgets import QMessageBox

def run_stm_scan():
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Information)
    msg.setWindowTitle("STM Scan")
    msg.setText("STM scan is being started.")
    msg.exec_()

