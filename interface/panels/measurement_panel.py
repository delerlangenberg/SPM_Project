# File: interface/panels/measurement_panel.py

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QMessageBox

class MeasurementPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.start_button = QPushButton("Start Measurement")
        self.start_button.clicked.connect(self.start_measurement)
        layout.addWidget(self.start_button)

        self.stop_button = QPushButton("Stop Measurement")
        self.stop_button.clicked.connect(self.stop_measurement)
        layout.addWidget(self.stop_button)

        self.setLayout(layout)

    def start_measurement(self):
        QMessageBox.information(self, "Start Measurement", "Measurement started...")

    def stop_measurement(self):
        QMessageBox.information(self, "Stop Measurement", "Measurement stopped...")
