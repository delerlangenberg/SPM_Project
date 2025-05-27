# simulation/scan_simulator.py

import numpy as np
from simulation.virtual_tip import VirtualTip
from simulation.z_feedback_simulator import ZFeedbackSimulator


class ScanSimulator:
    """
    Simulates a 2D area scan by moving a virtual tip over a synthetic surface.
    Applies feedback regulation at each point.
    """

    def __init__(self, width=10.0, height=10.0, resolution=50, profile_type='bumps'):
        self.width = width
        self.height = height
        self.resolution = resolution
        self.dx = width / resolution
        self.dy = height / resolution

        self.surface = self.generate_surface(profile_type)
        self.tip = VirtualTip(surface=self.surface)
        self.feedback = ZFeedbackSimulator(setpoint=0.0)

        self.scan_data = np.zeros((resolution, resolution))

    def generate_surface(self, mode='bumps'):
        """
        Generate a synthetic 2D surface.
        Options: 'bumps', 'lines', 'wave', 'grid'
        """
        x = np.linspace(0, self.width, self.resolution)
        y = np.linspace(0, self.height, self.resolution)
        X, Y = np.meshgrid(x, y)

        if mode == 'bumps':
            Z = 0.5 * np.sin(2 * np.pi * X / self.width) * np.cos(2 * np.pi * Y / self.height)
        elif mode == 'wave':
            Z = np.sin(2 * np.pi * X / self.width)
        elif mode == 'grid':
            Z = (np.mod(X, 1.0) + np.mod(Y, 1.0)) * 0.2
        elif mode == 'lines':
            Z = 0.3 * np.sin(4 * np.pi * X / self.width)
        else:
            Z = np.zeros_like(X)

        return Z

    def reset(self):
        """
        Reset the simulator state and feedback loop.
        """
        self.tip = VirtualTip(surface=self.surface)
        self.feedback.reset()
        self.scan_data = np.zeros((self.resolution, self.resolution))

    def run_scan(self, callback=None):
        """
        Simulate a full 2D scan and return topography array.
        """
        for iy in range(self.resolution):
            for ix in range(self.resolution):
                z_measured = self.tip.measure(ix, iy)
                z_corrected = self.feedback.update(z_measured)

                self.scan_data[iy, ix] = z_corrected

                if callback:
                    callback(ix, iy, z_corrected)

        return self.scan_data
