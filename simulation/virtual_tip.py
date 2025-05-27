# simulation/virtual_tip.py

import numpy as np
from math import sin, cos, pi

class VirtualTip:
    """
    Simulates SPM tip response by probing a mathematical surface model.
    Used in simulation mode to mimic topography and feedback input.
    """

    def __init__(self, mode="default"):
        self.mode = mode
        self.noise_level = 0.01  # microns, can be dynamically adjusted
        self.set_surface(mode)

    def set_surface(self, mode):
        """
        Initialize or switch the virtual surface model.
        """
        self.mode = mode

        if mode == "default":
            self.surface_fn = lambda x, y: 0.2 * sin(0.5 * x) * cos(0.5 * y)
        elif mode == "steps":
            self.surface_fn = lambda x, y: 0.2 * np.floor(x) % 1
        elif mode == "random":
            rng = np.random.default_rng(seed=42)
            self.random_field = rng.random((100, 100)) * 0.5
            self.surface_fn = self._random_surface_lookup
        elif mode == "pit":
            self.surface_fn = lambda x, y: -0.3 * np.exp(-((x-5)**2 + (y-5)**2)/2)
        else:
            raise ValueError(f"Unsupported surface mode: {mode}")

    def _random_surface_lookup(self, x, y):
        """
        Bilinear lookup from the random height field.
        """
        i = int(np.clip(x, 0, 99))
        j = int(np.clip(y, 0, 99))
        return self.random_field[i, j]

    def get_height(self, x, y):
        """
        Return simulated surface height at position (x, y) with optional noise.
        """
        base = self.surface_fn(x, y)
        noise = np.random.normal(0, self.noise_level)
        return base + noise
