# simulation/z_signal_simulator.py

import numpy as np

class ZSignalSimulator:
    """
    Simulates the Z signal feedback based on a virtual sample surface.
    Useful for testing feedback control and scan behavior.
    """

    def __init__(self, surface_fn=None, noise_level=0.01):
        self.noise_level = noise_level
        self.surface_fn = surface_fn if surface_fn is not None else self.default_surface

    def default_surface(self, x, y):
        """
        Default heightmap: sinusoidal surface + Gaussian bump
        """
        surface = 0.5 * np.sin(2 * np.pi * x / 10) + 0.3 * np.cos(2 * np.pi * y / 10)
        bump = np.exp(-((x - 5)**2 + (y - 5)**2) / 4)
        return surface + 0.8 * bump

    def get_height(self, x, y):
        """
        Return simulated height value at (x, y) with noise
        """
        true_height = self.surface_fn(x, y)
        noise = np.random.normal(0, self.noise_level)
        return true_height + noise

    def simulate_feedback_response(self, x, y, setpoint):
        """
        Return the simulated Z-position needed to reach the tunneling setpoint
        """
        surface_height = self.get_height(x, y)
        z_pos = surface_height + np.random.normal(0, 0.005)
        return z_pos
