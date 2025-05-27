# z_simulator.py

import numpy as np

class ZAxisSimulator:
    def __init__(self, noise_level=0.01):
        self.true_position = 0.0
        self.noise_level = noise_level

    def set_true_position(self, position):
        self.true_position = position

    def measure(self):
        noise = np.random.normal(0, self.noise_level)
        return self.true_position + noise


from PyQt5.QtWidgets import QDialog, QLabel, QVBoxLayout

def launch_z_simulator():
    dlg = QDialog()
    dlg.setWindowTitle("Z Simulator")
    layout = QVBoxLayout()
    layout.addWidget(QLabel("Z Simulator UI not yet implemented."))
    dlg.setLayout(layout)
    dlg.exec_()
