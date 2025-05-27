# D:/Documents/Project/SPM/core/scan/scan_simulator.py

import numpy as np
from PyQt5.QtWidgets import QDialog, QLabel, QVBoxLayout


class ScanSimulator:
    def __init__(self, scan_range=(0, 10), resolution=100, noise_level=0.05):
        self.scan_range = scan_range
        self.resolution = resolution
        self.noise_level = noise_level
        self.generated_data = []

    def generate_scan_data(self):
        """Generate simulated scan data with noise."""
        x = np.linspace(self.scan_range[0], self.scan_range[1], self.resolution)
        y = np.sin(x) + np.random.normal(0, self.noise_level, self.resolution)
        self.generated_data = list(zip(x, y))
        return self.generated_data


def launch_scan_simulator():
    """Launch a placeholder GUI for the scan simulator."""
    dlg = QDialog()
    dlg.setWindowTitle("Scan Simulator")
    layout = QVBoxLayout()
    layout.addWidget(QLabel("Scan Simulator UI not yet implemented."))
    dlg.setLayout(layout)
    dlg.exec_()
