# control/afm_noncontact_mode.py

import numpy as np

from .base_scan_mode import BaseScanMode

from core.z_control.z_interface import get_z_driver






class AFMNonContactMode(BaseScanMode):
    """
    Simulates AFM Non-Contact Mode, where tip oscillation amplitude is used for surface interaction.
    """

    def __init__(self, config=None, hardware_mode=False):
        super().__init__(config)
        self.hardware_mode = hardware_mode
        self.z_driver = get_z_driver(hardware_mode)
        self.x_range = config.get("x_range", 10)
        self.y_range = config.get("y_range", 10)
        self.resolution = config.get("resolution", 100)
        self.amplitude_setpoint = config.get("setpoint", 0.8)
        self.x_step = self.x_range / self.resolution
        self.y_step = self.y_range / self.resolution
        self.simulated_surface = None

    def initialize(self):
        print("[AFMNonContactMode] Initialization...")
        self.simulated_surface = self._generate_simulated_amplitude_map()
        self.current_position = (0, 0)
        self.data_buffer.clear()
        self.z_driver.initialize()

    def perform_step(self):
        x, y = self.current_position
        amplitude = self._simulate_amplitude_signal(x, y)
        z = self._amplitude_to_z(amplitude)
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
        print("[AFMNonContactMode] Finalizing scan...")
        self.z_driver.shutdown()

    def _generate_simulated_amplitude_map(self):
        x = np.linspace(0, self.x_range, self.resolution)
        y = np.linspace(0, self.y_range, self.resolution)
        X, Y = np.meshgrid(x, y)
        Z = 1.0 - 0.2 * np.cos(2 * np.pi * X / self.x_range) * np.cos(2 * np.pi * Y / self.y_range)
        return Z

    def _simulate_amplitude_signal(self, x, y):
        ix = min(int((x / self.x_range) * (self.resolution - 1)), self.resolution - 1)
        iy = min(int((y / self.y_range) * (self.resolution - 1)), self.resolution - 1)
        return self.simulated_surface[iy, ix]

    def _amplitude_to_z(self, amplitude):
        # Simple inverse mapping for simulation purposes
        return 1.0 / (amplitude + 0.01)

def run_noncontact_scan():
    print('Stub function run_noncontact_scan called.')
