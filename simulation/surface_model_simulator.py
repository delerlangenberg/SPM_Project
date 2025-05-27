# simulation/surface_model_simulator.py

import numpy as np

class SurfaceModelSimulator:
    """
    Simulates a virtual sample surface for STM/AFM scanning.
    Provides height (Z) values at any (X, Y) position.
    """

    def __init__(self, model_type="sinusoidal", size=(100, 100), amplitude=1.0, frequency=1.0):
        self.model_type = model_type.lower()
        self.size = size  # (width, height)
        self.amplitude = amplitude
        self.frequency = frequency
        self.surface = self._generate_surface()

    def _generate_surface(self):
        """
        Create a surface height map based on the selected model.
        Returns a 2D numpy array of Z heights.
        """
        x = np.linspace(0, 2 * np.pi * self.frequency, self.size[0])
        y = np.linspace(0, 2 * np.pi * self.frequency, self.size[1])
        X, Y = np.meshgrid(x, y)

        if self.model_type == "sinusoidal":
            Z = self.amplitude * np.sin(X) * np.sin(Y)

        elif self.model_type == "random":
            Z = self.amplitude * np.random.rand(*self.size)

        elif self.model_type == "step":
            Z = np.where(X < np.pi, 0, self.amplitude)

        elif self.model_type == "pit":
            Z = -self.amplitude * np.exp(-((X - np.pi)**2 + (Y - np.pi)**2))

        elif self.model_type == "ridge":
            Z = self.amplitude * np.exp(-((Y - np.pi)**2))

        else:
            raise ValueError(f"Unknown surface model type: {self.model_type}")

        return Z

    def get_height(self, x_idx, y_idx):
        """
        Returns the Z height at given (x, y) index.
        Ensures coordinates are within surface bounds.
        """
        x_idx = np.clip(x_idx, 0, self.size[0] - 1)
        y_idx = np.clip(y_idx, 0, self.size[1] - 1)
        return self.surface[y_idx, x_idx]
