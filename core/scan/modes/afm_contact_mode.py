# core/scan/afm_contact_mode.py

import numpy as np

from core.scan.base_scan_mode import BaseScanMode
from core.z_control.z_interface import get_z_driver




class AFMContactMode(BaseScanMode):
    """
    Implements AFM Contact Mode scan behavior.
    """

    def __init__(self, config=None, hardware_mode=False):
        super().__init__(config)
        self.hardware_mode = hardware_mode
        self.z_driver = get_z_driver(hardware_mode)
        self.x_range = config.get("x_range", 10)
        self.y_range = config.get("y_range", 10)
        self.resolution = config.get("resolution", 100)
        self.force_setpoint = config.get("setpoint", 1.0)
        self.x_step = self.x_range / self.resolution
        self.y_step = self.y_range / self.resolution
        self.simulated_surface = None

    def initialize(self):
        print("[AFMContactMode] Initialization...")
        self.simulated_surface = self._generate_simulated_surface()
        self.current_position = (0, 0)
        self.data_buffer.clear()
        self.z_driver.initialize()

    def perform_step(self):
        x, y = self.current_position
        z = self._simulate_contact_force(x, y)
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
        print("[AFMContactMode] Finalizing scan...")
        self.z_driver.shutdown()

    def _generate_simulated_surface(self):
        x = np.linspace(0, self.x_range, self.resolution)
        y = np.linspace(0, self.y_range, self.resolution)
        X, Y = np.meshgrid(x, y)
        Z = 1.5 * np.sin(3 * np.pi * X / self.x_range) * np.sin(2 * np.pi * Y / self.y_range)
        return Z

    def _simulate_contact_force(self, x, y):
        ix = min(int((x / self.x_range) * (self.resolution - 1)), self.resolution - 1)
        iy = min(int((y / self.y_range) * (self.resolution - 1)), self.resolution - 1)
        return self.simulated_surface[iy, ix]

def run_contact_scan():
    print('Stub function run_contact_scan called.')
