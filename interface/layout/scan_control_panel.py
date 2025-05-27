from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QGridLayout, QLabel, QLineEdit, QPushButton, QComboBox, QGroupBox
)
from PyQt5.QtCore import pyqtSignal

class ScanControlPanel(QWidget):
    """
    Scan Settings and Adaptation Configuration Panel.
    Allows fine control of scan speed, adaptation modes, and constraints.
    """
    update_scan_speed = pyqtSignal(float)
    update_scan_parameters = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        layout.addWidget(self._build_scan_speed_controls())
        layout.addWidget(self._build_scan_mode_settings())

        self.setLayout(layout)

    def _build_scan_speed_controls(self):
        group = QGroupBox("Scan Speed & Adaptation")
        grid = QGridLayout()

        self.scan_speed_input = QLineEdit("3.333")  # Default scan speed in µm/s
        self.line_freq_input = QLineEdit("0")  # Default line delay

        grid.addWidget(QLabel("Scan Speed [µm/s]"), 0, 0)
        grid.addWidget(self.scan_speed_input, 0, 1)
        grid.addWidget(QLabel("Line Delay [ms]"), 1, 0)
        grid.addWidget(self.line_freq_input, 1, 1)

        apply_btn = QPushButton("Apply Speed Settings")
        apply_btn.clicked.connect(self.apply_speed_settings)
        grid.addWidget(apply_btn, 2, 0, 1, 2)

        group.setLayout(grid)
        return group

    def _build_scan_mode_settings(self):
        group = QGroupBox("Scan Constraints & Adaptation")
        grid = QGridLayout()

        self.scan_mode_selector = QComboBox()
        self.scan_mode_selector.addItems(["Constant Line Frequency", "Fixed Scan Speed", "Adaptive Mode"])

        self.constraint_selector = QComboBox()
        self.constraint_selector.addItems(["None", "High Precision", "Drift Compensation"])

        grid.addWidget(QLabel("Scan Adaptation Mode"), 0, 0)
        grid.addWidget(self.scan_mode_selector, 0, 1)
        grid.addWidget(QLabel("Scan Constraint"), 1, 0)
        grid.addWidget(self.constraint_selector, 1, 1)

        apply_btn = QPushButton("Apply Scan Settings")
        apply_btn.clicked.connect(self.apply_scan_parameters)
        grid.addWidget(apply_btn, 2, 0, 1, 2)

        group.setLayout(grid)
        return group

    def apply_speed_settings(self):
        """Emit signal to update scan speed settings."""
        speed = float(self.scan_speed_input.text())
        self.update_scan_speed.emit(speed)

    def apply_scan_parameters(self):
        """Emit signal to update scan adaptation settings."""
        params = {
            "scan_mode": self.scan_mode_selector.currentText(),
            "constraint": self.constraint_selector.currentText(),
            "line_delay": float(self.line_freq_input.text())
        }
        self.update_scan_parameters.emit(params)
        
        
def launch_scan_control():
    from PyQt5.QtWidgets import QDialog, QVBoxLayout
    from .scan_control_panel import ScanControlPanel  # Adjust if needed
    dialog = QDialog()
    dialog.setWindowTitle("Scan Control Panel")
    layout = QVBoxLayout(dialog)
    layout.addWidget(ScanControlPanel())
    dialog.setLayout(layout)
    dialog.exec_()
