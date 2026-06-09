# z_driver_simulated.py

import time

class SimulatedZDriver:
    def __init__(self):
        self.position = 0.0

    def move_to(self, z_position):
        time.sleep(0.01)  # Simulate delay
        self.position = z_position

    def get_position(self):
        return self.position

    def close(self):
        pass  # Nothing to close
