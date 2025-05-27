# File: interface/panels/simulation_panel.py

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QMessageBox

class SimulationPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.start_button = QPushButton("Start Simulation")
        self.start_button.clicked.connect(self.start_simulation)
        layout.addWidget(self.start_button)

        self.stop_button = QPushButton("Stop Simulation")
        self.stop_button.clicked.connect(self.stop_simulation)
        layout.addWidget(self.stop_button)

        self.setLayout(layout)

    def start_simulation(self):
        QMessageBox.information(self, "Start Simulation", "Simulation started...")

    def stop_simulation(self):
        QMessageBox.information(self, "Stop Simulation", "Simulation stopped...")
