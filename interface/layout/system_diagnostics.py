from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QGridLayout, QLabel, QTextEdit, QGroupBox, QPushButton
)
from PyQt5.QtCore import QTimer, QDateTime

class SystemDiagnostics(QWidget):
    """
    Real-time System Diagnostics & Error Tracking Panel.
    Displays logs, system status, and scan performance metrics.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        self._init_timer()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        layout.addWidget(self._build_status_info())
        layout.addWidget(self._build_log_panel())

        self.setLayout(layout)

    def _build_status_info(self):
        group = QGroupBox("System Status & Performance")
        grid = QGridLayout()

        self.system_status_label = QLabel("Status: Normal")
        self.scan_latency_label = QLabel("Scan Latency: --- ms")
        self.drift_status_label = QLabel("Drift Compensation: ---")
        self.timestamp_label = QLabel("Last Update: ---")

        grid.addWidget(QLabel("System Health"), 0, 0)
        grid.addWidget(self.system_status_label, 0, 1)
        grid.addWidget(QLabel("Scan Latency"), 1, 0)
        grid.addWidget(self.scan_latency_label, 1, 1)
        grid.addWidget(QLabel("Drift Compensation"), 2, 0)
        grid.addWidget(self.drift_status_label, 2, 1)
        grid.addWidget(QLabel("Timestamp"), 3, 0)
        grid.addWidget(self.timestamp_label, 3, 1)

        group.setLayout(grid)
        return group

    def _build_log_panel(self):
        group = QGroupBox("System Log & Error Reports")
        layout = QVBoxLayout()

        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)

        self.clear_log_btn = QPushButton("Clear Logs")
        self.clear_log_btn.clicked.connect(self.clear_logs)

        layout.addWidget(self.log_display)
        layout.addWidget(self.clear_log_btn)
        group.setLayout(layout)

        return group

    def _init_timer(self):
        """ Update timestamp and system monitoring every 2 seconds """
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_system_status)
        self.timer.start(2000)

    def update_system_status(self):
        """ Simulates system monitoring updates """
        current_time = QDateTime.currentDateTime().toString("yyyy-MM-dd HH:mm:ss")
        self.timestamp_label.setText(f"Last Update: {current_time}")

        # Simulated drift and scan latency updates
        self.scan_latency_label.setText(f"Scan Latency: {self.get_random_latency()} ms")
        self.drift_status_label.setText(f"Drift Compensation: {self.get_random_drift_status()}")

        # Log simulated update
        self.append_log(f"[{current_time}] System check: Normal.")

    def get_random_latency(self):
        """ Simulated latency tracking for demonstration """
        import random
        return random.randint(10, 50)

    def get_random_drift_status(self):
        """ Simulated drift tracking """
        import random
        return random.choice(["Stable", "Minor Drift", "Correction Applied"])

    def append_log(self, message):
        """ Adds an entry to the system log """
        self.log_display.append(message)

    def clear_logs(self):
        """ Clears log entries """
        self.log_display.clear()

def launch_diagnostics():
    print('Diagnostics panel not yet implemented')
