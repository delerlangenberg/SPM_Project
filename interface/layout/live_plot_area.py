from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QGroupBox, QStatusBar, QHBoxLayout, QFrame
from PyQt5.QtCore import QTimer, QTime
import pyqtgraph as pg

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel

class StatusBar(QStatusBar):
    """
    Real-time Status and Diagnostic Bar for SPM Interface.
    Displays scan state, tip feedback, and live time.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        self._init_timer()

    def _build_ui(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 2, 5, 2)
        layout.setSpacing(15)

        self.status_label = QLabel("Status: Idle")
        self.z_feedback_label = QLabel("Z: --- nm")
        self.amplitude_label = QLabel("Amp: --- mV")
        self.time_label = QLabel()

        for label in (self.status_label, self.z_feedback_label, self.amplitude_label, self.time_label):
            label.setFrameStyle(QFrame.Panel | QFrame.Sunken)
            layout.addWidget(label)

        # Adding layout to StatusBar
        self.setLayout(layout)

    def _init_timer(self):
        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self._update_time)
        self.clock_timer.start(1000)  # Update every second
        self._update_time()

    def _update_time(self):
        current_time = QTime.currentTime().toString("HH:mm:ss")
        self.time_label.setText(f"Time: {current_time}")

    def update_status(self, message: str):
        """Update the general scan status label."""
        self.status_label.setText(f"Status: {message}")

    def update_z_feedback(self, value: float):
        """Update the Z-axis feedback value in nm."""
        self.z_feedback_label.setText(f"Z: {value:.2f} nm")

    def update_amplitude(self, value: float):
        """Update the measured amplitude in mV (AFM mode)."""
        self.amplitude_label.setText(f"Amp: {value:.1f} mV")

class LivePlotArea(QWidget):
    """
    Advanced real-time monitoring panel for SPM systems.
    Displays Z-position, amplitude trace, tip current, and system status.
    """
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setMinimumHeight(350)
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # Status Bar at the top
        self.status_bar = StatusBar(self)
        self.layout.addWidget(self.status_bar)

        # Group container for plots
        self.plot_group = QGroupBox("Live Feedback Monitor")
        self.plot_layout = QVBoxLayout()

        # Z Position Plot (Red Curve)
        self.z_plot = pg.PlotWidget(title="Z Position [nm]")
        self.z_curve = self.z_plot.plot(pen=pg.mkPen('r', width=2))
        self.z_data = []

        # Amplitude Plot (Blue Curve)
        self.amp_plot = pg.PlotWidget(title="Oscillation Amplitude [a.u.]")
        self.amp_curve = self.amp_plot.plot(pen=pg.mkPen('b', width=2))
        self.amp_data = []

        # Tip Current Plot (Green Curve)
        self.tip_current_plot = pg.PlotWidget(title="Tip Current [nA]")
        self.tip_curve = self.tip_current_plot.plot(pen=pg.mkPen('g', width=2))
        self.tip_current_data = []

        # Organizing plot structure
        self.plot_layout.addWidget(self.z_plot)
        self.plot_layout.addWidget(self.amp_plot)
        self.plot_layout.addWidget(self.tip_current_plot)
        self.plot_group.setLayout(self.plot_layout)
        self.layout.addWidget(self.plot_group)

    def update_data(self, z_value, amp_value, tip_current_value):
        """
        Update the plot curves and status labels with new values.
        Call this from your feedback or scan engine.
        """
        self.z_data.append(z_value)
        self.amp_data.append(amp_value)
        self.tip_current_data.append(tip_current_value)

        if len(self.z_data) > 150:  # Keeps buffers optimized
            self.z_data.pop(0)
            self.amp_data.pop(0)
            self.tip_current_data.pop(0)

        self.z_curve.setData(self.z_data)
        self.amp_curve.setData(self.amp_data)
        self.tip_curve.setData(self.tip_current_data)

        # Update status bar with latest feedback values
        self.status_bar.update_z_feedback(z_value)
        self.status_bar.update_amplitude(amp_value)
        

# Enables menu_bar to launch this as a standalone dialog
def launch_live_plot():
    from PyQt5.QtWidgets import QDialog, QVBoxLayout
    dialog = QDialog()
    dialog.setWindowTitle("Live Plot Area")
    layout = QVBoxLayout(dialog)
    layout.addWidget(LivePlotArea())
    dialog.setLayout(layout)
    dialog.exec_()
