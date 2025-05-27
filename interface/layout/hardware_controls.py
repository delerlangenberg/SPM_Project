# Located in interface/layout/hardware_controls.py

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton,
    QGroupBox, QSlider, QCheckBox, QGridLayout
)
from PyQt5.QtCore import Qt

# Inside interface/layout/hardware_controls.py

from PyQt5.QtWidgets import QDialog, QVBoxLayout

def launch_hardware_controls():
    from .hardware_controls import HardwareControlPanel  # Adjust only if needed
    dialog = QDialog()
    dialog.setWindowTitle("Hardware Controls")
    layout = QVBoxLayout(dialog)
    layout.addWidget(HardwareControlPanel())
    dialog.setLayout(layout)
    dialog.exec_()


class HardwareControlPanel(QWidget):
    # Located in interface/layout/hardware_controls.py
    def __init__(self):
        super().__init__()
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout()

        # Example group box for actuator control
        actuator_group = QGroupBox("Actuator Controls")
        actuator_layout = QGridLayout()
        actuator_layout.addWidget(QLabel("Voltage:"), 0, 0)
        actuator_slider = QSlider(Qt.Horizontal)
        actuator_slider.setRange(0, 100)
        actuator_layout.addWidget(actuator_slider, 0, 1)
        actuator_group.setLayout(actuator_layout)

        # Example group box for status indicators
        status_group = QGroupBox("Hardware Status")
        status_layout = QVBoxLayout()
        status_layout.addWidget(QCheckBox("Z Scanner Connected"))
        status_layout.addWidget(QCheckBox("ADC Interface Ready"))
        status_group.setLayout(status_layout)

        # Example button panel
        button = QPushButton("Initialize Hardware")
        button.clicked.connect(self._on_initialize_clicked)

        layout.addWidget(actuator_group)
        layout.addWidget(status_group)
        layout.addWidget(button)

        self.setLayout(layout)

    def _on_initialize_clicked(self):
        print("Stub: Initialize hardware clicked.")
