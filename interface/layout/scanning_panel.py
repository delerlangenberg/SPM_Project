from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QGridLayout, QLabel, QLineEdit, QPushButton,
    QComboBox, QGroupBox, QHBoxLayout
)
from PyQt5.QtCore import pyqtSignal

class ScanningPanel(QWidget):
    """
    High-level STM/AFM Scan Configuration Panel.
    Supports mode switching, parameter control, scan movement, and real-time adjustments.
    """
    start_scan = pyqtSignal()
    pause_scan = pyqtSignal()
    resume_scan = pyqtSignal()
    stop_scan = pyqtSignal()
    move_scan = pyqtSignal(float, float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        layout.addWidget(self._build_scan_parameters_group())
        layout.addWidget(self._build_movement_controls())
        layout.addLayout(self._build_button_row())

    def _build_scan_parameters_group(self):
        group = QGroupBox("Scan Configuration")
        grid = QGridLayout()

        self.mode_selector = QComboBox()
        self.mode_selector.addItems(["STM", "AFM Contact", "AFM Non-Contact"])

        self.size_input = QLineEdit("100")  # Default scan area in nm
        self.res_input = QLineEdit("300")  # Default resolution (px)

        grid.addWidget(QLabel("Scan Mode"), 0, 0)
        grid.addWidget(self.mode_selector, 0, 1)
        grid.addWidget(QLabel("Scan Size [nm]"), 1, 0)
        grid.addWidget(self.size_input, 1, 1)
        grid.addWidget(QLabel("Resolution [px]"), 2, 0)
        grid.addWidget(self.res_input, 2, 1)

        group.setLayout(grid)
        return group

    def _build_movement_controls(self):
        group = QGroupBox("Scan Position Control")
        grid = QGridLayout()

        self.x_position_input = QLineEdit("0.0")
        self.y_position_input = QLineEdit("0.0")
        self.angle_input = QLineEdit("0")

        move_btn = QPushButton("Move Scan Area")
        move_btn.clicked.connect(lambda: self.move_scan.emit(float(self.x_position_input.text()), float(self.y_position_input.text())))

        grid.addWidget(QLabel("X Position [nm]"), 0, 0)
        grid.addWidget(self.x_position_input, 0, 1)
        grid.addWidget(QLabel("Y Position [nm]"), 1, 0)
        grid.addWidget(self.y_position_input, 1, 1)
        grid.addWidget(QLabel("Scan Angle [°]"), 2, 0)
        grid.addWidget(self.angle_input, 2, 1)
        grid.addWidget(move_btn, 3, 0, 1, 2)

        group.setLayout(grid)
        return group

    def _build_button_row(self):
        layout = QHBoxLayout()

        self.start_btn = QPushButton("Start Scan")
        self.pause_btn = QPushButton("Pause Scan")
        self.resume_btn = QPushButton("Resume Scan")
        self.stop_btn = QPushButton("Stop Scan")

        self.start_btn.clicked.connect(self.start_scan.emit)
        self.pause_btn.clicked.connect(self.pause_scan.emit)
        self.resume_btn.clicked.connect(self.resume_scan.emit)
        self.stop_btn.clicked.connect(self.stop_scan.emit)

        layout.addWidget(self.start_btn)
        layout.addWidget(self.pause_btn)
        layout.addWidget(self.resume_btn)
        layout.addWidget(self.stop_btn)

        return layout

    def get_scan_parameters(self):
        """Returns current scan parameters as a dictionary."""
        return {
            "mode": self.mode_selector.currentText(),
            "size_nm": float(self.size_input.text()),
            "resolution_px": int(self.res_input.text()),
            "x_position": float(self.x_position_input.text()),
            "y_position": float(self.y_position_input.text()),
            "angle": int(self.angle_input.text())
        }
        
        
from PyQt5.QtWidgets import QDialog, QVBoxLayout

def launch_scanning_panel():
    from .scanning_panel import ScanningPanel  # Adjust this if necessary
    dialog = QDialog()
    dialog.setWindowTitle("Scanning Panel")
    layout = QVBoxLayout(dialog)
    layout.addWidget(ScanningPanel())
    dialog.setLayout(layout)
    dialog.exec_()
