# simulation/scan_pattern_simulator.py

import numpy as np

class ScanPatternSimulator:
    """
    Generates simulated scan patterns for test scanning.
    Supports raster (serpentine), fast-line, and spiral modes.
    """

    def __init__(self, scan_size=10.0, resolution=100, mode="raster"):
        self.scan_size = scan_size      # in micrometers (or arbitrary units)
        self.resolution = resolution    # number of points per axis
        self.mode = mode.lower()        # scan mode string

    def generate_pattern(self):
        if self.mode == "raster":
            return self._raster_pattern()
        elif self.mode == "spiral":
            return self._spiral_pattern()
        elif self.mode == "profile_x":
            return self._line_profile(axis='x')
        elif self.mode == "profile_y":
            return self._line_profile(axis='y')
        else:
            raise ValueError(f"Unknown scan mode: {self.mode}")

    def _raster_pattern(self):
        """
        Standard serpentine raster scan (alternating direction).
        Returns list of (x, y) tuples.
        """
        x_vals = np.linspace(0, self.scan_size, self.resolution)
        y_vals = np.linspace(0, self.scan_size, self.resolution)
        pattern = []

        for i, y in enumerate(y_vals):
            if i % 2 == 0:
                row = [(x, y) for x in x_vals]
            else:
                row = [(x, y) for x in reversed(x_vals)]
            pattern.extend(row)

        return pattern

    def _spiral_pattern(self):
        """
        Generates an Archimedean spiral scan pattern.
        """
        points = self.resolution ** 2
        r_max = self.scan_size / 2
        theta = np.linspace(0, 10 * np.pi, points)
        r = np.linspace(0, r_max, points)
        x = r * np.cos(theta) + r_max
        y = r * np.sin(theta) + r_max
        return list(zip(x, y))

    def _line_profile(self, axis='x'):
        """
        Generates a single line scan along x or y axis.
        """
        points = self.resolution
        if axis == 'x':
            x = np.linspace(0, self.scan_size, points)
            y = np.full_like(x, self.scan_size / 2)
        else:
            y = np.linspace(0, self.scan_size, points)
            x = np.full_like(y, self.scan_size / 2)

        return list(zip(x, y))
