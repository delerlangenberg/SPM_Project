# simulation/mock_motor_driver.py

import time

class MockMotorDriver:
    """
    Simulates stepper motor control for X, Y, Z axes.
    Provides position tracking and simulated movement delays.
    """

    def __init__(self):
        self.position = {"x": 0.0, "y": 0.0, "z": 0.0}
        self.step_size = 0.1  # um per step (fine-tune per calibration)
        self.speed_delay = 0.001  # seconds per step (for realism)

    def move_to(self, axis, target_pos):
        """
        Simulate smooth motion of a motor to a given position on specified axis.
        """
        if axis not in self.position:
            raise ValueError(f"Invalid axis: {axis}. Must be one of x, y, z.")

        current = self.position[axis]
        step_direction = 1 if target_pos > current else -1

        steps = int(abs(target_pos - current) / self.step_size)
        for _ in range(steps):
            current += step_direction * self.step_size
            self.position[axis] = round(current, 4)
            time.sleep(self.speed_delay)  # simulate time taken per step

        self.position[axis] = round(target_pos, 4)

    def get_position(self):
        """Returns the current (x, y, z) position of the simulated tip."""
        return self.position.copy()

    def reset_position(self):
        """Reset all motor axes to zero position."""
        self.position = {"x": 0.0, "y": 0.0, "z": 0.0}
