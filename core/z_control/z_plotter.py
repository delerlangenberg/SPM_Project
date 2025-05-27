# z_plotter.py


# core/z_control/z_plotter.py

def launch_z_plotter():
    print("[Z-Plotter] Visualizing Z-axis behavior...")

import matplotlib.pyplot as plt

class ZDataPlotter:
    def __init__(self):
        self.z_positions = []
        self.timestamps = []

    def add_data_point(self, position, timestamp):
        self.z_positions.append(position)
        self.timestamps.append(timestamp)

    def plot(self):
        plt.figure()
        plt.plot(self.timestamps, self.z_positions)
        plt.xlabel("Time (s)")
        plt.ylabel("Z Position (nm)")
        plt.title("Z Position Over Time")
        plt.grid(True)
        plt.show()

def launch_z_plotter():
    print('Stub function launch_z_plotter called.')
