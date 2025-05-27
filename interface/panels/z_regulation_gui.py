# File: interface/panels/z_regulation_gui.py

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QRadioButton, QPushButton,
    QHBoxLayout, QGroupBox, QComboBox, QDoubleSpinBox, QProgressBar
)
from PyQt5.QtCore import Qt, QTimer
import pyqtgraph as pg  # Placeholder for future real-time plot
import random

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QGroupBox, QRadioButton, QPushButton, QHBoxLayout

class ZRegulationPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Z-Regulation Control Panel")
        self.setMinimumSize(500, 400)

        # Single main layout
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # Status Badge
        self.status_badge = QLabel("Status: Ready")
        self.status_badge.setStyleSheet("color: green; font-weight: bold")
        self.layout.addWidget(self.status_badge)

        # Mode Group
        self.mode_group = QGroupBox("Z Regulation Mode")
        mode_layout = QHBoxLayout()
        self.const_height_radio = QRadioButton("Constant Height")
        self.const_current_radio = QRadioButton("Constant Current")
        self.confirm_mode_btn = QPushButton("Confirm Mode")
        self.confirm_mode_btn.clicked.connect(self.confirm_mode)
        mode_layout.addWidget(self.const_height_radio)
        mode_layout.addWidget(self.const_current_radio)
        mode_layout.addWidget(self.confirm_mode_btn)
        self.mode_group.setLayout(mode_layout)
        self.layout.addWidget(self.mode_group)

        # Feedback Label
        self.feedback_label = QLabel("Select a regulation mode and confirm.")
        self.feedback_label.setAlignment(Qt.AlignCenter)
        self.feedback_label.setStyleSheet("color: gray")
        self.layout.addWidget(self.feedback_label)

        # Settings Group
        self.settings_group = QGroupBox("Regulation Parameters")
        self.settings_group.setEnabled(False)
        settings_layout = QVBoxLayout()

        self.mode_dropdown = QComboBox()
        self.mode_dropdown.addItems(["Manual", "Auto", "Approach"])
        self.mode_dropdown.currentTextChanged.connect(self.update_feedback_label)

        self.z_setpoint_spin = QDoubleSpinBox()
        self.z_setpoint_spin.setPrefix("Z Height (nm): ")
        self.z_setpoint_spin.setRange(0.1, 100.0)
        self.z_setpoint_spin.setSingleStep(0.1)
        self.z_setpoint_spin.setEnabled(False)

        self.current_setpoint_spin = QDoubleSpinBox()
        self.current_setpoint_spin.setPrefix("Current (nA): ")
        self.current_setpoint_spin.setRange(0.01, 10.0)
        self.current_setpoint_spin.setSingleStep(0.01)
        self.current_setpoint_spin.setEnabled(False)

        self.approach_speed_spin = QDoubleSpinBox()
        self.approach_speed_spin.setPrefix("Speed: ")
        self.approach_speed_spin.setRange(0.1, 10.0)
        self.approach_speed_spin.setSingleStep(0.1)
        self.approach_speed_spin.setValue(1.0)

        # Control Buttons
        self.start_btn = QPushButton("Start Approach")
        self.start_btn.setEnabled(False)
        self.start_btn.clicked.connect(self.run_approach_simulation)

        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_approach)

        self.resume_btn = QPushButton("Resume")
        self.resume_btn.setEnabled(False)
        self.resume_btn.clicked.connect(self.resume_approach)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.clicked.connect(self.cancel_approach)

        self.abort_btn = QPushButton("Abort All")
        self.abort_btn.setStyleSheet("background-color: red; color: white; font-weight: bold")
        self.abort_btn.setEnabled(False)
        self.abort_btn.clicked.connect(self.abort_all)

        # Add widgets to settings layout
        settings_layout.addWidget(self.mode_dropdown)
        settings_layout.addWidget(self.z_setpoint_spin)
        settings_layout.addWidget(self.current_setpoint_spin)
        settings_layout.addWidget(self.approach_speed_spin)
        settings_layout.addWidget(self.start_btn)
        settings_layout.addWidget(self.stop_btn)
        settings_layout.addWidget(self.resume_btn)
        settings_layout.addWidget(self.cancel_btn)
        settings_layout.addWidget(self.abort_btn)

        self.settings_group.setLayout(settings_layout)
        self.layout.addWidget(self.settings_group)

        # Progress Bar
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.layout.addWidget(self.progress)

        # Timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_simulation)

        # Initialize feedback data lists
        self.feedback_data = []
        self.time_data = []
        
        # Setup your plot widget here (using pyqtgraph or matplotlib)
        self.plot_widget = pg.PlotWidget()
        self.layout.addWidget(self.plot_widget)
        self.feedback_curve = self.plot_widget.plot([], [])

        self.t = 0

    # ... rest of your methods unchanged, but use self.layout.addWidget instead of self.layout (method) ...



    def confirm_mode(self):
        if self.const_height_radio.isChecked():
            mode = "Constant Height"
            self.z_setpoint_spin.setEnabled(True)
            self.current_setpoint_spin.setEnabled(False)
        elif self.const_current_radio.isChecked():
            mode = "Constant Current"
            self.z_setpoint_spin.setEnabled(False)
            self.current_setpoint_spin.setEnabled(True)
        else:
            self.feedback_label.setText("Please select a mode.")
            self.feedback_label.setStyleSheet("color: red")
            return

        self.settings_group.setEnabled(True)
        self.start_btn.setEnabled(True)
        self.feedback_label.setStyleSheet("color: blue")
        self.feedback_label.setText(f"Confirmed Mode: {mode}")

    def update_feedback_label(self, mode):
        self.feedback_label.setText(f"Regulation Mode: {mode}")
        
        

    def run_approach_simulation(self):
        self.t = 0
        self.progress.setValue(0)
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.cancel_btn.setEnabled(True)
        self.resume_btn.setEnabled(False)
        self.abort_btn.setEnabled(True)
        self.timer.start(100)
        
            
    def update_approach_feedback(self):
        self.t += 0.1
        new_feedback = random.uniform(0.0, 1.0)  # Simulated feedback signal
        self.feedback_data.append(new_feedback)
        self.time_data.append(self.t)

        self.feedback_curve.setData(self.time_data, self.feedback_data)
        self.progress.setValue(min(int((self.t / 10) * 100), 100))

        if self.t >= 10:  # End of simulated approach
            self.timer.stop()
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            self.cancel_btn.setEnabled(False)
            self.resume_btn.setEnabled(False)
            self.feedback_label.setText("Approach Complete")



    def update_simulation(self):
        self.t += 5
        if self.t > 100:
            self.timer.stop()
            self.feedback_label.setText("Approach complete.")
            self.feedback_label.setStyleSheet("color: green")
            self.stop_btn.setEnabled(False)
            self.cancel_btn.setEnabled(False)
            return
        self.progress.setValue(self.t)

    def stop_approach(self):
        self.timer.stop()
        self.feedback_label.setText("Approach paused.")
        self.resume_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)

    def resume_approach(self):
        self.timer.start(100)
        self.feedback_label.setText("Approach resumed.")
        self.resume_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)

    def cancel_approach(self):
        self.timer.stop()
        self.t = 0
        self.progress.setValue(0)
        self.feedback_label.setText("Approach canceled.")
        self.stop_btn.setEnabled(False)
        self.resume_btn.setEnabled(False)
        self.cancel_btn.setEnabled(False)
        self.abort_btn.setEnabled(False)

    def abort_all(self):
        self.timer.stop()
        self.t = 0
        self.progress.setValue(0)
        self.feedback_label.setText("All operations aborted.")
        self.feedback_label.setStyleSheet("color: red")
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)
        self.resume_btn.setEnabled(False)
        self.cancel_btn.setEnabled(False)
        self.abort_btn.setEnabled(False)

# part 2
    def stop_approach(self):
        self.timer.stop()
        self.stop_btn.setEnabled(False)
        self.resume_btn.setEnabled(True)
        self.feedback_label.setText("Approach Paused")

    def resume_approach(self):
        self.timer.start(100)
        self.stop_btn.setEnabled(True)
        self.resume_btn.setEnabled(False)
        self.feedback_label.setText("Approach Resumed")

    def cancel_approach(self):
        self.timer.stop()
        self._reset_feedback_plot()
        self._reset_control_state()
        self.feedback_label.setText("Approach Cancelled")

    def abort_all(self):
        self.timer.stop()
        self._reset_feedback_plot()
        self.feedback_label.setStyleSheet("color: red; font-weight: bold")
        self.feedback_label.setText("ABORTED: All regulation halted.")
        self._reset_controls()

    def _reset_controls(self):
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.resume_btn.setEnabled(False)
        self.cancel_btn.setEnabled(False)
        self.const_height_radio.setEnabled(True)
        self.const_current_radio.setEnabled(True)
        self.confirm_mode_btn.setEnabled(True)
        self.z_setpoint_spin.setEnabled(False)
        self.current_setpoint_spin.setEnabled(False)
        self.settings_group.setEnabled(False)

   
    def _reset_control_state(self):
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.resume_btn.setEnabled(False)
        self.cancel_btn.setEnabled(False)
        self.const_height_radio.setEnabled(True)
        self.const_current_radio.setEnabled(True)
        self.confirm_mode_btn.setEnabled(True)
        
    def _reset_feedback_plot(self):
        self.feedback_data.clear()
        self.time_data.clear()
        self.feedback_curve.setData([], [])
        self.progress.setValue(0)

           

    def confirm_mode(self):
        if self.const_height_radio.isChecked():
            mode = "Constant Height"
            self.z_setpoint_spin.setEnabled(True)
            self.current_setpoint_spin.setEnabled(False)
        elif self.const_current_radio.isChecked():
            mode = "Constant Current"
            self.current_setpoint_spin.setEnabled(True)
            self.z_setpoint_spin.setEnabled(False)
        else:
            mode = None

        if mode:
            self.settings_group.setEnabled(True)
            self.start_btn.setEnabled(True)
            self.feedback_label.setStyleSheet("")
            self.feedback_label.setText(f"Confirmed Mode: {mode}")
        else:
            self.feedback_label.setStyleSheet("color: red; font-weight: bold")
            self.feedback_label.setText("Please select a mode first.")


# part3
    def update_simulated_feedback(self):
        # Maintain a rolling buffer of 500 points
        if len(self.time_data) > 500:
            self.time_data = self.time_data[-500:]
            self.feedback_data = self.feedback_data[-500:]

        self.t += 0.1
        mode = self.mode_dropdown.currentText()
        speed = self.approach_speed_spin.value()

        # Determine target and variability based on mode
        if self.const_height_radio.isChecked():
            target = self.z_setpoint_spin.value()
            variability = 0.5 if mode == "Auto" else 0.2
        elif self.const_current_radio.isChecked():
            target = self.current_setpoint_spin.value()
            variability = 0.2 if mode == "Auto" else 0.05
        else:
            target = 0
            variability = 0

        increment = speed * 0.05  # approach step size
        last_value = self.feedback_data[-1] if self.feedback_data else 0
        signal = min(target, last_value + random.uniform(0, increment + variability))

        self.feedback_data.append(signal)
        self.time_data.append(self.t)
        self.feedback_curve.setData(self.time_data, self.feedback_data)
        self.progress.setValue(int(min(100, (signal / target) * 100)) if target > 0 else 0)

        if signal >= target and target > 0:
            self.timer.stop()
            self._reset_controls()
            self.feedback_label.setStyleSheet("color: green; font-weight: bold")
            self.feedback_label.setText(f"Approach Complete: Reached {signal:.2f}")

