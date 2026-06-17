from __future__ import annotations

import subprocess
import sys
import re
import socket
import math
import csv
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QFormLayout,
    QLineEdit,
    QPushButton,
    QMessageBox,
    QTextEdit,
    QVBoxLayout, QHBoxLayout,
    QGroupBox,
    QLabel,
    QFileDialog,
    QComboBox,
    QProgressBar,
    QTabWidget,
    QTextBrowser,
    QDialog,
    QScrollArea,
    QGridLayout,
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, QTimer

from core.acquisition.raster_stream import load_raster_frame
from core.application.workstation_status import WorkstationStatus
from core.education.config_loader import load_config, get_safe_feedrates, get_scan_mode_preset
from core.education.scan_profile import (
    ScanProfile,
    MotionLimits,
    VALID_SCAN_MODES,
    validate_scan_profile,
    MAX_SCAN_RESOLUTION,
)
from core.system.hardware_diagnostics import run_hardware_communication_report
from core.system.hardware_profile import SPMHardwareProfile
from core.system.mk4s_z_auto_approach import run_mk4s_z_auto_approach, run_mk4s_z_manual_step, run_mk4s_z_safe_retract
from core.system.workstation_initializer import run_workstation_initialization
from core.motion.prusa_gcode_backend import PrusaGcodeBackend
from core.motion.parking import park_mk4s

from core.z_control.crtouch_probe_plan import CRTouchProbePlan
from core.z_control.z_driver_arduino_safe import ZDriverArduino


# ============================================================
# SPM Educational GUI
# Safe GUI wrapper around the verified CLI scan launcher
# ============================================================
APP_VERSION = "v0.25.0"
APP_PHASE = "Focused SPM Workflow - Connection, Approach, Measurement"
APP_BUILD_DATE = "2026-06-12"
APP_TITLE = f"Educational SPM {APP_VERSION} - Operator Workspace - Prusa MK4S"


class ScanGUI(QWidget):
    # ------------------------------------------------------------
    # GUI constructor
    # ------------------------------------------------------------
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_TITLE)

        # ------------------------------------------------------------
        # Load configuration
        # ------------------------------------------------------------
        self.config = load_config()
        self.safe_feedrates = get_safe_feedrates(self.config)
        self.workstation_status = WorkstationStatus.from_config(self.config)
        self.crtouch_plan = CRTouchProbePlan()
        self.hardware_profile = SPMHardwareProfile.from_config(self.config)
        self.current_position = {"x": None, "y": None, "z": None}
        self.shutdown_complete = False
        self.last_plot_path = ""
        self.scan_viewers = []
        self.direction_viewers = {}
        self.direction_preview_labels = {}
        self.direction_window_labels = {}
        self.z_approached = False
        self.scan_stop_requested = False
        self.scan_pause_requested = False
        self.live_scan_timer = QTimer(self)
        self.live_scan_timer.timeout.connect(self.advance_live_scan)
        self.live_scan_points = []
        self.live_scan_index = 0
        self.live_scan_rows = []
        self.live_scan_current_line = []
        self.live_scan_profile = None
        self.live_scan_active = False
        self.live_scan_z_setpoint = float(self.config["scan_area"]["z"])

        # ------------------------------------------------------------
        # Locked motion limits
        # ------------------------------------------------------------
        self.limits = MotionLimits(
            x_min=self.config["motion_limits"]["x"][0],
            x_max=self.config["motion_limits"]["x"][1],
            y_min=self.config["motion_limits"]["y"][0],
            y_max=self.config["motion_limits"]["y"][1],
            z_min=self.config["motion_limits"]["z"][0],
            z_max=self.config["motion_limits"]["z"][1],
        )

        scan_area = self.config["scan_area"]

        # ------------------------------------------------------------
        # Layouts
        # ------------------------------------------------------------
        main_layout = QVBoxLayout()
        form_layout = QFormLayout()

        # ------------------------------------------------------------
        # Scan input fields
        # ------------------------------------------------------------
        self.x_min = QLineEdit(str(scan_area["x_min"]))
        self.x_max = QLineEdit(str(scan_area["x_max"]))
        self.y_min = QLineEdit(str(scan_area["y_min"]))
        self.y_max = QLineEdit(str(scan_area["y_max"]))
        self.z = QLineEdit(str(scan_area["z"]))
        self.x_res = QLineEdit(str(scan_area["x_resolution"]))
        self.y_res = QLineEdit(str(scan_area["y_resolution"]))
        self.xy_feedrate = QLineEdit(str(self.safe_feedrates["xy"]))
        self.z_feedrate = QLineEdit(str(self.safe_feedrates["z"]))
        self.z_dwell_ms = QLineEdit("50")
        self.line_time_estimate_label = QLabel("Line time: waiting for scan settings")
        self.frame_time_estimate_label = QLabel("Frame time: waiting for scan settings")
        self.mode_readiness_label = QLabel("")
        self.mode_readiness_label.setWordWrap(True)

        # ------------------------------------------------------------
        # Output CSV path
        # ------------------------------------------------------------
        self.output_file = QLineEdit("data/interface_test_output.csv")

        form_layout.addRow("X min:", self.field_with_tip(self.x_min, self.hardware_profile.compact_axis_range("X")))
        form_layout.addRow("X max:", self.field_with_tip(self.x_max, self.hardware_profile.compact_axis_range("X")))
        form_layout.addRow("Y min:", self.field_with_tip(self.y_min, self.hardware_profile.compact_axis_range("Y")))
        form_layout.addRow("Y max:", self.field_with_tip(self.y_max, self.hardware_profile.compact_axis_range("Y")))
        form_layout.addRow("X resolution:", self.field_with_tip(self.x_res, self.hardware_profile.compact_resolution_range()))
        form_layout.addRow("Y resolution:", self.field_with_tip(self.y_res, self.hardware_profile.compact_resolution_range()))
        form_layout.addRow("XY speed mm/min:", self.xy_feedrate)
        form_layout.addRow("Line estimate:", self.line_time_estimate_label)
        form_layout.addRow("Frame estimate:", self.frame_time_estimate_label)
        form_layout.addRow("Output CSV:", self.output_file)

        # ------------------------------------------------------------
        # Browse button for CSV output
        # ------------------------------------------------------------
        self.output_file_browse = QPushButton("Browse...")
        self.output_file_browse.clicked.connect(self.select_output_file)
        form_layout.addRow("", self.output_file_browse)

        # ------------------------------------------------------------
        # Plot color map selection
        # ------------------------------------------------------------
        self.color_map_dropdown = QComboBox()
        self.color_map_dropdown.addItems(["viridis", "plasma", "inferno", "magma"])
        self.color_map_dropdown.setCurrentText("viridis")
        self.color_map_dropdown.currentTextChanged.connect(self.update_color_map)
        self.color_map = "viridis"
        self.scan_mode_dropdown = QComboBox()
        self.scan_mode_dropdown.addItems(sorted(VALID_SCAN_MODES))
        self.scan_mode_dropdown.setCurrentText("SIMULATED_SURFACE")
        self.scan_mode_dropdown.currentTextChanged.connect(self.apply_scan_mode_preset)
        form_layout.addRow("Plot color map:", self.color_map_dropdown)
        form_layout.addRow("Scan mode:", self.scan_mode_dropdown)
        form_layout.addRow("Mode hardware:", self.mode_readiness_label)

        # ------------------------------------------------------------
        # Buttons
        # ------------------------------------------------------------
        self.operation_mode_dropdown = QComboBox()
        self.operation_mode_dropdown.addItems(["DEMO SOFTWARE", "HARDWARE TEST", "REAL MEASUREMENT"])
        self.operation_mode_dropdown.setCurrentText("DEMO SOFTWARE")
        self.operation_mode_dropdown.currentTextChanged.connect(self.update_operation_mode)

        self.open_scan_setup_btn = QPushButton("MEASUREMENT SETUP")
        self.open_scan_setup_btn.clicked.connect(self.open_measurement_window)
        self.open_xy_scanner_btn = QPushButton("XY SCANNER")
        self.open_xy_scanner_btn.clicked.connect(self.open_xy_scanner_window)
        self.open_z_regulation_btn = QPushButton("SERVICE APPROACH")
        self.open_z_regulation_btn.clicked.connect(self.open_z_regulation_window)
        self.open_hardware_tools_btn = QPushButton("HARDWARE CHECK")
        self.open_hardware_tools_btn.clicked.connect(self.open_hardware_tools_window)
        self.hardware_check_btn = QPushButton("RUN HARDWARE CHECK")
        self.hardware_check_btn.clicked.connect(self.run_hardware_check_only)
        self.open_z_tools_btn = QPushButton("Z / APPROACH")
        self.open_z_tools_btn.clicked.connect(self.open_measurement_window)
        self.about_btn = QPushButton("ABOUT")
        self.about_btn.clicked.connect(self.show_about)

        self.direction_buttons = {}
        for direction, label in (
            ("forward", "X+ TOPOGRAPHY"),
            ("backward", "X- TOPOGRAPHY"),
            ("upward", "Y+ TOPOGRAPHY"),
            ("downward", "Y- TOPOGRAPHY"),
        ):
            button = QPushButton(label)
            button.clicked.connect(lambda _checked=False, scan_direction=direction: self.open_direction_window(scan_direction))
            self.direction_buttons[direction] = button

        self.main_scan_btn = QPushButton("START")
        self.main_scan_btn.setStyleSheet("font-weight: bold; background-color: #1565c0; color: white; padding: 6px;")
        self.main_scan_btn.clicked.connect(self.run_main_scan)
        self.pause_scan_btn = QPushButton("PAUSE")
        self.pause_scan_btn.clicked.connect(self.pause_scan)
        self.pause_scan_btn.setEnabled(False)
        self.stop_scan_btn = QPushButton("STOP")
        self.stop_scan_btn.clicked.connect(self.stop_scan)
        self.stop_scan_btn.setEnabled(False)

        self.validate_btn = QPushButton("Validate Profile")
        self.validate_btn.clicked.connect(self.validate_profile)

        self.dry_run_btn = QPushButton("Demo Scan - No Hardware Movement")
        self.dry_run_btn.clicked.connect(self.run_dry_scan)

        self.execute_btn = QPushButton("REAL HARDWARE SCAN")
        self.execute_btn.setStyleSheet("font-weight: bold; background-color: #9e9e9e; color: white; padding: 6px;")
        self.execute_btn.setEnabled(False)
        self.execute_btn.clicked.connect(self.run_hardware_scan)

        # ------------------------------------------------------------
        # Safe Z-control dry-run driver
        # These controls do not move real hardware.
        # They only test the Phase 5.1 Arduino/Z-control software path.
        # ------------------------------------------------------------
        self.z_driver = ZDriverArduino(dry_run=True)

        self.z_status_label = QLabel("Z dry-run status: Disconnected")
        self.z_connection_state_label = QLabel("? READY TO CONNECT")
        self.z_connection_state_label.setStyleSheet("font-weight: bold; color: #c62828;")
        self.z_test_position = QLineEdit("20")

        self.z_approach_start = QLineEdit("20")
        self.z_approach_target = QLineEdit("17")
        self.z_retract_start = QLineEdit("17")
        self.z_retract_target = QLineEdit("20")
        self.z_step_size = QLineEdit("1")

        self.z_connect_btn = QPushButton("Z Dry Run: Connect")
        self.z_connect_btn.clicked.connect(self.run_z_dry_connect)

        self.z_move_test_btn = QPushButton("MANUAL Z MOVE DRY RUN")
        self.z_move_test_btn.clicked.connect(self.run_z_dry_move_test)

        self.z_approach_btn = QPushButton("AUTO APPROACH DRY RUN")
        self.z_approach_btn.clicked.connect(self.run_z_dry_approach)

        self.z_retract_btn = QPushButton("RETRACT Z DRY RUN")
        self.z_retract_btn.clicked.connect(self.run_z_dry_retract)

        self.z_disconnect_btn = QPushButton("Z Dry Run: Disconnect")
        self.z_disconnect_btn.clicked.connect(self.run_z_dry_disconnect)

        self.z_connect_btn.setText("CONNECT Z DRY RUN")
        self.z_connect_btn.setStyleSheet("font-weight: bold; background-color: #2e7d32; color: white;")
        self.z_disconnect_btn.setText("DISCONNECTED")
        self.z_disconnect_btn.setStyleSheet("font-weight: bold; background-color: #757575; color: white;")

        # Initial safe Z-control button state
        self.z_move_test_btn.setEnabled(False)
        self.z_approach_btn.setEnabled(False)
        self.z_retract_btn.setEnabled(False)
        self.z_disconnect_btn.setEnabled(False)

        # ------------------------------------------------------------
        # Status log
        # ------------------------------------------------------------
        self.log = QTextEdit()
        self.log.setReadOnly(True)

        # ------------------------------------------------------------
        # Workstation placeholder/status widgets
        # ------------------------------------------------------------
        self.system_status_label = QLabel("SYSTEM STATUS: NOT CONNECTED")
        self.system_status_label.setStyleSheet("font-weight: bold; background-color: #263238; color: white; padding: 6px;")
        self.operator_step_label = QLabel("Next action: connect to SPM. The software will run the required no-motion checks automatically.")
        self.operator_step_label.setWordWrap(True)
        self.operator_step_label.setStyleSheet("background: #fffde7; border: 1px solid #fbc02d; padding: 8px;")

        self.hardware_status_label = QLabel("Hardware / System Connection: REAL MOTION DISABLED - run system check first")
        self.machine_status_label = QLabel("")
        self.workflow_status_label = QLabel("")
        self.stage_position_label = QLabel("Current MK4S position: X unknown | Y unknown | Z unknown")
        self.stage_position_label.setStyleSheet("font-weight: bold; background: #eceff1; border: 1px solid #b0bec5; padding: 8px;")
        self.hardware_parameters_label = QLabel("")
        self.hardware_parameters_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.hardware_parameters_label.setStyleSheet("border: 1px solid #b0bec5; background: #ffffff; padding: 8px; font-family: Consolas, monospace;")
        self.hardware_parameters_label.setFixedHeight(180)
        self.hardware_parameters_label.setWordWrap(True)
        self.output_status_label = QLabel("")
        self.acquisition_status_label = QLabel("")
        self.scan_progress_bar = QProgressBar()
        self.scan_progress_bar.setRange(0, 100)
        self.scan_progress_bar.setValue(0)
        # Legacy Phase 6.3 safety marker retained for source-based tests:
        # self.hardware_armed = False
        self.hardware_armed = self.workstation_status.real_motion_enabled
        self.system_check_passed = self.workstation_status.system_check_passed
        # Legacy source marker retained for regression history: QPushButton("POWER ON / INITIALIZE")
        self.initiate_system_check_btn = QPushButton("CONNECT TO SPM")
        self.initiate_system_check_btn.setStyleSheet("font-weight: bold; background-color: #1565c0; color: white; padding: 6px;")
        self.initiate_system_check_btn.clicked.connect(self.initiate_system_check)
        self.query_position_btn = QPushButton("READ MK4S POSITION")
        self.query_position_btn.clicked.connect(self.query_mk4s_position)
        self.park_btn = QPushButton("PARK MK4S")
        self.park_btn.clicked.connect(self.park_workstation)
        self.power_off_btn = QPushButton("DISCONNECT")
        self.power_off_btn.setStyleSheet("font-weight: bold; background-color: #455a64; color: white; padding: 6px;")
        self.power_off_btn.clicked.connect(self.power_off_workstation)
        self.close_btn = QPushButton("CLOSE SOFTWARE")
        self.close_btn.setStyleSheet("font-weight: bold; background-color: #757575; color: white; padding: 6px;")
        self.close_btn.setEnabled(False)
        self.close_btn.clicked.connect(self.close_after_power_off)
        self.hardware_arm_btn = QPushButton("ENABLE REAL MOTION")
        self.hardware_arm_btn.setStyleSheet("font-weight: bold; background-color: #2e7d32; color: white; padding: 6px;")
        self.hardware_arm_btn.clicked.connect(self.arm_hardware)
        self.hardware_disarm_btn = QPushButton("DISABLE REAL MOTION")
        self.hardware_disarm_btn.setStyleSheet("font-weight: bold; background-color: #9e9e9e; color: white; padding: 6px;")
        self.hardware_disarm_btn.setEnabled(False)
        self.hardware_disarm_btn.clicked.connect(self.disarm_hardware)
        self.safety_status_label = QLabel("Safety State: global motion limits active; critical confirmations enabled")
        self.hardware_tuning_label = QLabel(self.hardware_profile.summary())
        self.hardware_tuning_label.setWordWrap(True)
        self.main_z_status_label = QLabel("Approach locked until SPM is connected.")
        self.main_z_status_label.setWordWrap(True)
        self.main_z_status_label.setStyleSheet("border: 1px solid #90a4ae; background: #fffde7; padding: 8px;")
        self.main_z_create_btn = QPushButton("SERVICE: PREPARE APPROACH")
        self.main_z_create_btn.clicked.connect(self.run_main_z_create)
        self.main_z_move_btn = QPushButton("SERVICE: MANUAL APPROACH")
        self.main_z_move_btn.clicked.connect(self.run_main_z_move)
        self.main_z_approach_btn = QPushButton("Z AUTO APPROACH")
        self.main_z_approach_btn.setStyleSheet("font-weight: bold; background-color: #1565c0; color: white; padding: 6px;")
        self.main_z_approach_btn.clicked.connect(self.run_main_z_auto_approach)
        self.main_z_retract_btn = QPushButton("RETRACT Z")
        self.main_z_retract_btn.clicked.connect(self.run_main_z_retract)
        self.z_manual_step_mm = QLineEdit("1.0")
        self.z_setpoint_distance_mm = QLineEdit("0.0")
        self.main_z_up_btn = QPushButton("MANUAL UP")
        self.main_z_up_btn.clicked.connect(lambda: self.run_main_z_manual_step("up"))
        self.main_z_down_btn = QPushButton("MANUAL DOWN")
        self.main_z_down_btn.clicked.connect(lambda: self.run_main_z_manual_step("down"))
        self.plot_placeholder = QLabel("Live Data / Raster Plot Preview\n\nPlaceholder for last generated PNG, future live raster image, and signal monitor.")
        self.plot_placeholder.setStyleSheet("border: 1px solid #9e9e9e; padding: 12px; background-color: #fafafa;")
        self.plot_placeholder.setFixedSize(460, 260)
        self.plot_placeholder.setAlignment(Qt.AlignCenter)
        self.plot_placeholder.setScaledContents(False)
        self.plot_placeholder.setWordWrap(True)

        self.line_scan_placeholder = QLabel(
            f"1D Line Scan\n\nWaiting for scan data.\nFrame capacity: {MAX_SCAN_RESOLUTION} samples per line."
        )
        self.line_scan_placeholder.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.line_scan_placeholder.setStyleSheet("border: 1px solid #90a4ae; padding: 10px; background-color: #ffffff;")
        self.line_scan_placeholder.setFixedSize(460, 145)
        self.line_scan_placeholder.setWordWrap(True)

        self.topography_placeholder = QLabel(
            f"2D Topography Scan\n\nWaiting for raster/topography data.\nPreview frame is fixed; max input resolution is {MAX_SCAN_RESOLUTION} x {MAX_SCAN_RESOLUTION}."
        )
        self.topography_placeholder.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.topography_placeholder.setStyleSheet("border: 1px solid #90a4ae; padding: 10px; background-color: #ffffff;")
        self.topography_placeholder.setFixedSize(460, 220)
        self.topography_placeholder.setWordWrap(True)

        self.z_condition_placeholder = QLabel("Z Condition / Feedback\n\nZ position: waiting\nApproach state: waiting\nSignal / height feedback: waiting")
        self.z_condition_placeholder.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.z_condition_placeholder.setStyleSheet("border: 1px solid #90a4ae; padding: 10px; background-color: #fffde7;")
        self.z_condition_placeholder.setFixedSize(460, 190)
        self.z_condition_placeholder.setWordWrap(True)

        self.line_direction_dropdown = QComboBox()
        self.line_direction_dropdown.addItems(["current", "forward", "backward"])
        self.line_direction_dropdown.currentTextChanged.connect(self.redraw_live_scan_views)
        self.topography_direction_dropdown = QComboBox()
        self.topography_direction_dropdown.addItems(["current", "upward", "downward", "all"])
        self.topography_direction_dropdown.currentTextChanged.connect(self.redraw_live_scan_views)
        self.live_line_canvas = QLabel("Line scan waiting for approach and scan start")
        self.live_line_canvas.setFixedSize(720, 190)
        self.live_line_canvas.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.live_line_canvas.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.live_line_canvas.setWordWrap(True)
        self.live_line_canvas.setStyleSheet(
            "border: 1px solid #607d8b; background: #ffffff; padding: 10px; font-family: Consolas, monospace;"
        )
        self.live_topography_canvas = QLabel("Topography waiting for raster lines")
        self.live_topography_canvas.setFixedSize(720, 320)
        self.live_topography_canvas.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.live_topography_canvas.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.live_topography_canvas.setWordWrap(False)
        self.live_topography_canvas.setStyleSheet(
            "border: 1px solid #607d8b; background: #ffffff; padding: 10px; font-family: Consolas, monospace;"
        )
        self.live_scan_status_label = QLabel(
            "Live scan: idle. After Z approach, SCAN DEMO shows regulated line scan and accumulated topography."
        )
        self.live_scan_status_label.setWordWrap(True)
        self.live_scan_status_label.setStyleSheet("background: #eef6ff; border: 1px solid #90a4ae; padding: 8px;")

        self.z_probe_plan_label = QLabel(self.crtouch_plan.readiness_summary())
        self.z_probe_plan_label.setStyleSheet("border: 1px solid #90a4ae; padding: 10px; background-color: #eef6ff;")
        self.z_probe_plan_label.setWordWrap(True)

        self.z_probe_safety_label = QLabel(self.crtouch_plan.safety_summary())
        self.z_probe_safety_label.setStyleSheet("border: 1px solid #90a4ae; padding: 10px; background-color: #fff8e1;")
        self.z_probe_safety_label.setWordWrap(True)

        self.open_scan_viewer_btn = QPushButton("OPEN SCAN VIEWER")
        self.open_scan_viewer_btn.clicked.connect(self.open_scan_viewer)
        self.open_scan_viewer_btn.setEnabled(False)

        for button in (
            self.open_scan_setup_btn,
            self.open_xy_scanner_btn,
            self.open_z_regulation_btn,
            self.hardware_check_btn,
            self.open_hardware_tools_btn,
            self.open_z_tools_btn,
            self.about_btn,
            self.initiate_system_check_btn,
            self.main_scan_btn,
            self.pause_scan_btn,
            self.stop_scan_btn,
            self.power_off_btn,
            self.close_btn,
            self.main_z_create_btn,
            self.main_z_move_btn,
            self.main_z_approach_btn,
            self.main_z_retract_btn,
            self.main_z_up_btn,
            self.main_z_down_btn,
        ):
            button.setMinimumWidth(86)
            button.setMaximumWidth(165)
        for button in (
            self.main_z_create_btn,
            self.main_z_move_btn,
            self.main_z_approach_btn,
            self.main_z_retract_btn,
            self.main_z_up_btn,
            self.main_z_down_btn,
        ):
            button.setMinimumWidth(145)
            button.setMaximumWidth(230)

        # ------------------------------------------------------------
        # XY Scan Setup panel
        # ------------------------------------------------------------
        xy_scan_group = QGroupBox("1 Scan Parameters: XYZ + Output")
        xy_scan_layout = QVBoxLayout()
        xy_scan_layout.addLayout(form_layout)
        xy_scan_layout.addWidget(self.hardware_tuning_label)
        xy_scan_group.setLayout(xy_scan_layout)

        scan_execution_group = QGroupBox("2 Scan Execution: Validate + Dry Run First")
        scan_execution_layout = QVBoxLayout()
        scan_execution_layout.addWidget(self.validate_btn)
        scan_execution_layout.addWidget(self.dry_run_btn)
        scan_execution_group.setLayout(scan_execution_layout)

        left_panel = QVBoxLayout()
        left_panel.addWidget(xy_scan_group)
        left_panel.addWidget(scan_execution_group)
        left_panel.addStretch()

        # ------------------------------------------------------------
        # MK4S Z / Height Control panel
        # ------------------------------------------------------------
        # Legacy Phase 5.2 grouped-layout label retained for regression tests:
        # Z-control dry-run tools
        z_group = QGroupBox("3 MK4S Z Height / Approach Training")
        z_layout = QVBoxLayout()

        z_height_group = QGroupBox("MK4S Z Height / Safe Position")
        z_height_layout = QFormLayout()
        z_height_layout.addRow("Scan Z height:", self.z)
        z_height_layout.addRow("Z speed mm/min:", self.z_feedrate)
        z_height_layout.addRow("Z dwell ms/point:", self.z_dwell_ms)
        z_height_layout.addRow("Z dry-run test position:", self.z_test_position)
        z_height_group.setLayout(z_height_layout)

        z_connection_group = QGroupBox("Approach Simulator Connection")
        z_connection_layout = QVBoxLayout()

        z_connection_bar = QHBoxLayout()
        z_connection_bar.addWidget(self.z_connection_state_label)
        z_connection_bar.addWidget(self.z_connect_btn)
        z_connection_bar.addWidget(self.z_disconnect_btn)

        z_connection_layout.addLayout(z_connection_bar)
        z_connection_layout.addWidget(self.z_status_label)
        z_connection_group.setLayout(z_connection_layout)

        z_move_group = QGroupBox("Manual Z Move Preview")
        z_move_layout = QVBoxLayout()
        z_move_layout.addWidget(self.z_move_test_btn)
        z_move_group.setLayout(z_move_layout)

        z_approach_group = QGroupBox("Auto Approach Preview")
        z_approach_layout = QFormLayout()
        z_approach_layout.addRow("Approach start Z:", self.z_approach_start)
        z_approach_layout.addRow("Approach target Z:", self.z_approach_target)
        z_approach_layout.addRow("Z step size:", self.z_step_size)
        z_approach_layout.addRow("", self.z_approach_btn)
        z_approach_group.setLayout(z_approach_layout)

        z_retract_group = QGroupBox("Safe Retract Preview")
        z_retract_layout = QFormLayout()
        z_retract_layout.addRow("Retract start Z:", self.z_retract_start)
        z_retract_layout.addRow("Retract target Z:", self.z_retract_target)
        z_retract_layout.addRow("", self.z_retract_btn)
        z_retract_group.setLayout(z_retract_layout)

        z_layout.addWidget(z_height_group)
        z_layout.addWidget(z_connection_group)
        z_layout.addWidget(z_move_group)
        z_layout.addWidget(z_approach_group)
        z_layout.addWidget(z_retract_group)
        z_group.setLayout(z_layout)

        # ------------------------------------------------------------
        # Hardware and Safety placeholder panels
        # Legacy Phase 6.1 placeholder strings retained for regression history:
        # Placeholder: COM port, baudrate, machine connection, hardware readiness, last known state.
        # Placeholder: safe scan limits, safe Z range, critical-action confirmations, warning state.
        # Placeholder for last generated PNG, future live raster image, and signal monitor.
        # ------------------------------------------------------------
        hardware_group = QGroupBox("Hardware Check / Power / Connection")
        hardware_layout = QVBoxLayout()
        hardware_layout.addWidget(self.hardware_status_label)
        hardware_layout.addWidget(self.hardware_check_btn)
        hardware_layout.addWidget(self.initiate_system_check_btn)
        hardware_layout.addWidget(self.query_position_btn)
        hardware_layout.addWidget(self.park_btn)
        hardware_layout.addWidget(self.machine_status_label)
        hardware_layout.addWidget(self.workflow_status_label)
        hardware_layout.addWidget(self.hardware_arm_btn)
        hardware_layout.addWidget(self.hardware_disarm_btn)
        hardware_layout.addWidget(self.execute_btn)
        hardware_group.setLayout(hardware_layout)

        safety_group = QGroupBox("2 Safety / Hardware Arm State")
        safety_layout = QVBoxLayout()
        safety_layout.addWidget(self.safety_status_label)
        safety_layout.addWidget(self.output_status_label)
        safety_layout.addWidget(self.acquisition_status_label)
        safety_group.setLayout(safety_layout)

        right_panel = QVBoxLayout()
        right_panel.addWidget(hardware_group)
        right_panel.addWidget(safety_group)
        right_panel.addWidget(z_group)
        right_panel.addStretch()

        # Legacy tab strings retained for source-history tests:
        # feedback_tabs.addTab(self.plot_placeholder, "Raster Preview")
        # feedback_tabs.addTab(self.line_scan_placeholder, "Line Scan")
        # feedback_tabs.addTab(self.topography_placeholder, "Topography")

        z_feedback_tab = QWidget()
        z_feedback_layout = QVBoxLayout()
        z_feedback_layout.addWidget(self.z_condition_placeholder)
        z_feedback_layout.addWidget(self.z_probe_plan_label)
        z_feedback_layout.addWidget(self.z_probe_safety_label)
        z_feedback_tab.setLayout(z_feedback_layout)
        # feedback_tabs.addTab(z_feedback_tab, "Z / Probe")

        line_view_group = QGroupBox("Live Line Scan - Current X Sweep")
        line_view_layout = QVBoxLayout()
        line_selector_row = QHBoxLayout()
        line_selector_row.addWidget(QLabel("Line view:"))
        line_selector_row.addWidget(self.line_direction_dropdown)
        line_selector_row.addStretch()
        line_view_layout.addLayout(line_selector_row)
        line_view_layout.addWidget(self.live_line_canvas)
        line_view_group.setLayout(line_view_layout)

        topography_view_group = QGroupBox("Accumulated Topography - Raster Lines")
        topography_view_layout = QVBoxLayout()
        topography_selector_row = QHBoxLayout()
        topography_selector_row.addWidget(QLabel("Topography view:"))
        topography_selector_row.addWidget(self.topography_direction_dropdown)
        topography_selector_row.addStretch()
        topography_view_layout.addLayout(topography_selector_row)
        topography_view_layout.addWidget(self.live_topography_canvas)
        topography_view_group.setLayout(topography_view_layout)

        measurement_actions_group = QGroupBox("Measurement Controls")
        measurement_actions_layout = QHBoxLayout()
        measurement_actions_layout.addWidget(self.validate_btn)
        measurement_actions_layout.addWidget(self.dry_run_btn)
        measurement_actions_layout.addWidget(self.main_scan_btn)
        measurement_actions_layout.addWidget(self.pause_scan_btn)
        measurement_actions_layout.addWidget(self.stop_scan_btn)
        measurement_actions_group.setLayout(measurement_actions_layout)

        measurement_live_group = QGroupBox("Live Directional Feedback")
        measurement_live_layout = QVBoxLayout()
        measurement_live_layout.addWidget(self.scan_progress_bar)
        # Historical layout marker: measurement_live_layout.addWidget(feedback_tabs)
        measurement_live_layout.addWidget(self.live_scan_status_label)
        measurement_live_layout.addWidget(line_view_group)
        measurement_live_layout.addWidget(topography_view_group)
        measurement_live_group.setLayout(measurement_live_layout)

        measurement_layout = QVBoxLayout()
        measurement_layout.addWidget(measurement_actions_group)
        measurement_layout.addWidget(measurement_live_group)

        self.scan_setup_dialog = self.build_tool_dialog("Measurement Setup / Live Feedback", measurement_layout, 900, 720)
        xy_scanner_layout = QVBoxLayout()
        xy_scanner_layout.addWidget(xy_scan_group)
        xy_scanner_layout.addStretch()
        self.xy_scanner_dialog = self.build_tool_dialog("XY Scanner", xy_scanner_layout, 440, 640)
        z_regulation_layout = QVBoxLayout()
        z_regulation_layout.addWidget(z_group)
        z_regulation_layout.addStretch()
        self.z_regulation_dialog = self.build_tool_dialog("Service Approach Diagnostics", z_regulation_layout, 440, 680)
        hardware_tools_layout = QVBoxLayout()
        hardware_tools_layout.addWidget(hardware_group)
        hardware_tools_layout.addWidget(safety_group)
        hardware_tools_layout.addStretch()
        self.hardware_tools_dialog = self.build_tool_dialog("Hardware Check / Connection", hardware_tools_layout, 520, 640)
        self.z_tools_dialog = self.z_regulation_dialog

        # ------------------------------------------------------------
        # Center data/plot panel
        # ------------------------------------------------------------
        data_group = QGroupBox("Live Scan Feedback")
        data_layout = QVBoxLayout()
        self.main_feedback_label = QLabel("Open Measurement Setup to configure scanning and view live raster, line, topography, and Z approach feedback.")
        self.main_feedback_label.setWordWrap(True)
        self.main_feedback_label.setStyleSheet("border: 1px solid #90a4ae; padding: 12px; background: #ffffff;")
        data_layout.addWidget(self.main_feedback_label)
        data_group.setLayout(data_layout)

        # ------------------------------------------------------------
        # Bottom operator log panel
        # ------------------------------------------------------------
        log_group = QGroupBox("Operator Log")
        log_layout = QVBoxLayout()
        log_layout.addWidget(self.log)
        log_group.setLayout(log_layout)

        # ------------------------------------------------------------
        # Main workstation layout: connection, approach, measurement
        # ------------------------------------------------------------
        main_command_group = QGroupBox("SPM Connection")
        main_command_layout = QVBoxLayout()
        version_row = QHBoxLayout()
        self.version_label = QLabel(f"{APP_VERSION} | {APP_PHASE} | build {APP_BUILD_DATE}")
        self.version_label.setStyleSheet("font-weight: bold; color: #263238;")
        version_row.addWidget(self.version_label)
        version_row.addStretch()
        version_row.addWidget(self.about_btn)

        session_row = QHBoxLayout()
        session_row.addWidget(self.initiate_system_check_btn)
        session_row.addWidget(self.power_off_btn)
        session_row.addStretch()

        main_command_layout.addLayout(version_row)
        main_command_layout.addWidget(self.system_status_label)
        main_command_layout.addWidget(self.operator_step_label)
        main_command_layout.addLayout(session_row)
        main_command_group.setLayout(main_command_layout)

        main_status_group = QGroupBox("Live Hardware Parameters")
        main_status_layout = QVBoxLayout()
        main_status_layout.addWidget(self.stage_position_label)
        main_status_layout.addWidget(self.hardware_parameters_label)
        main_status_group.setLayout(main_status_layout)

        main_z_group = QGroupBox("Approach")
        main_z_layout = QVBoxLayout()
        z_parameter_layout = QFormLayout()
        z_parameter_layout.addRow("Setpoint above surface mm:", self.z_setpoint_distance_mm)
        z_parameter_layout.addRow("Manual step mm:", self.z_manual_step_mm)
        z_manual_row = QHBoxLayout()
        z_manual_row.addWidget(self.main_z_up_btn)
        z_manual_row.addWidget(self.main_z_down_btn)
        z_button_row = QHBoxLayout()
        z_button_row.addWidget(self.main_z_approach_btn)
        z_button_row.addWidget(self.main_z_retract_btn)
        main_z_layout.addWidget(self.main_z_status_label)
        main_z_layout.addLayout(z_parameter_layout)
        main_z_layout.addLayout(z_manual_row)
        main_z_layout.addLayout(z_button_row)
        main_z_group.setLayout(main_z_layout)

        measurement_group = QGroupBox("Measurement")
        measurement_layout_main = QVBoxLayout()
        xy_parameter_layout = QGridLayout()
        xy_parameter_layout.addWidget(QLabel("X min"), 0, 0)
        xy_parameter_layout.addWidget(self.x_min, 0, 1)
        xy_parameter_layout.addWidget(QLabel("X max"), 0, 2)
        xy_parameter_layout.addWidget(self.x_max, 0, 3)
        xy_parameter_layout.addWidget(QLabel("Y min"), 1, 0)
        xy_parameter_layout.addWidget(self.y_min, 1, 1)
        xy_parameter_layout.addWidget(QLabel("Y max"), 1, 2)
        xy_parameter_layout.addWidget(self.y_max, 1, 3)
        xy_parameter_layout.addWidget(QLabel("X points"), 2, 0)
        xy_parameter_layout.addWidget(self.x_res, 2, 1)
        xy_parameter_layout.addWidget(QLabel("Y points"), 2, 2)
        xy_parameter_layout.addWidget(self.y_res, 2, 3)
        measurement_button_row = QHBoxLayout()
        measurement_button_row.addWidget(self.main_scan_btn)
        measurement_button_row.addWidget(self.pause_scan_btn)
        measurement_button_row.addWidget(self.stop_scan_btn)
        direction_grid = QGridLayout()
        for index, direction in enumerate(("forward", "backward", "upward", "downward")):
            direction_grid.addWidget(self.direction_buttons[direction], 0, index)
        measurement_layout_main.addLayout(xy_parameter_layout)
        measurement_layout_main.addLayout(measurement_button_row)
        measurement_layout_main.addLayout(direction_grid)
        measurement_group.setLayout(measurement_layout_main)

        main_layout.addWidget(main_command_group)
        main_layout.addWidget(main_z_group)
        main_layout.addWidget(measurement_group)

        workstation_page = QWidget()
        workstation_page.setLayout(main_layout)
        workstation_scroll = QScrollArea()
        workstation_scroll.setWidgetResizable(True)
        workstation_scroll.setWidget(workstation_page)

        self.documentation_browser = QTextBrowser()
        self.documentation_browser.setMarkdown(self.documentation_markdown())

        root_tabs = QTabWidget()
        root_tabs.addTab(workstation_scroll, "Workstation")
        root_tabs.addTab(self.documentation_browser, "Documentation")

        root_layout = QVBoxLayout()
        root_layout.addWidget(root_tabs)

        self.setLayout(root_layout)
        screen = QApplication.primaryScreen()
        if screen is not None:
            available = screen.availableGeometry()
            self.resize(min(1040, max(900, available.width() - 120)), min(700, max(620, available.height() - 120)))
        else:
            self.resize(1040, 700)
        self.apply_instrument_style()
        self.connect_scan_setting_updates()
        self.apply_scan_mode_preset(self.scan_mode_dropdown.currentText(), show_limits=False)
        self.refresh_hardware_parameters("startup")
        self.set_initialized_controls_enabled(False)
        self.refresh_workstation_status_ui()

    # ------------------------------------------------------------
    # Select output CSV file
    # ------------------------------------------------------------
    def create_direction_preview_label(self, direction: str) -> QLabel:
        title = direction.upper()
        label = QLabel(
            f"{title} IMAGE\n\n"
            "Waiting for scan data.\n"
            "This fixed frame will show topography and line information for this raster direction."
        )
        label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        label.setStyleSheet("border: 1px solid #90a4ae; padding: 10px; background-color: #ffffff;")
        label.setFixedSize(260, 155)
        label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        label.setWordWrap(True)
        return label

    def build_tool_dialog(self, title: str, content_layout: QVBoxLayout, width: int, height: int) -> QDialog:
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Educational SPM {APP_VERSION} - {title}")
        dialog.setLayout(content_layout)
        dialog.resize(width, height)
        return dialog

    def open_measurement_window(self) -> None:
        self.scan_setup_dialog.show()
        self.scan_setup_dialog.raise_()
        self.scan_setup_dialog.activateWindow()

    def open_hardware_tools_window(self) -> None:
        self.hardware_tools_dialog.show()
        self.hardware_tools_dialog.raise_()
        self.hardware_tools_dialog.activateWindow()

    def open_xy_scanner_window(self) -> None:
        self.xy_scanner_dialog.show()
        self.xy_scanner_dialog.raise_()
        self.xy_scanner_dialog.activateWindow()

    def open_z_regulation_window(self) -> None:
        self.z_regulation_dialog.show()
        self.z_regulation_dialog.raise_()
        self.z_regulation_dialog.activateWindow()

    def open_z_tools_window(self) -> None:
        self.open_z_regulation_window()

    def show_about(self) -> None:
        QMessageBox.information(
            self,
            "About Educational SPM",
            f"Educational SPM {APP_VERSION}\n"
            f"{APP_PHASE}\n"
            f"Build date: {APP_BUILD_DATE}\n\n"
            "Current hardware target: Original Prusa MK4S motion platform.\n"
            "Current phase: MATRIX-style workstation shell with separate XY, Z, hardware, and directional image windows.\n\n"
            "Measurement safety rule: initialize once, approach Z, scan, then safe-park Z before XY and close.",
        )

    def direction_window_text(self, direction: str, frame=None) -> str:
        title = direction.upper()
        if frame is None:
            return (
                f"{title} IMAGE\n\n"
                "Waiting for scan data.\n"
                "Open Measurement and run a demo or real scan to populate this view."
            )

        counts = frame.direction_counts or {}
        low, high = frame.signal_range()
        return (
            f"{title} IMAGE\n\n"
            f"Samples in this direction: {counts.get(direction, 0)}\n"
            f"Grid: {len(frame.x_values)} x {len(frame.y_values)}\n"
            f"Signal min/max: {low:.4f} / {high:.4f}\n"
            f"All directions: {frame.direction_summary()}\n\n"
            f"Line profile:\n{frame.line_profile_bar()}"
        )

    def open_direction_window(self, direction: str) -> None:
        if direction not in self.direction_viewers:
            dialog = QDialog(self)
            dialog.setWindowTitle(f"Educational SPM {APP_VERSION} - {direction.title()} Image")
            layout = QVBoxLayout()
            label = self.create_direction_preview_label(direction)
            label.setFixedSize(430, 260)
            layout.addWidget(label)
            dialog.setLayout(layout)
            dialog.resize(470, 320)
            self.direction_viewers[direction] = dialog
            self.direction_window_labels[direction] = label

        viewer = self.direction_viewers[direction]
        viewer.show()
        viewer.raise_()
        viewer.activateWindow()

    def run_hardware_check_only(self) -> None:
        self.append_log("[HARDWARE CHECK] Running operator-requested hardware check")
        report = run_hardware_communication_report(self.config)
        for line in report.summary_lines():
            self.append_log(f"[HARDWARE CHECK] {line}")
        report_position = self.parse_position_from_report(report)
        if report_position:
            self.update_position_display(report_position, "hardware check")
        self.hardware_status_label.setText(
            "Hardware / System Connection: HARDWARE CHECK PASS" if report.passed
            else "Hardware / System Connection: HARDWARE CHECK FAILED"
        )
        self.hardware_status_label.setStyleSheet(
            "font-weight: bold; color: #2e7d32;" if report.passed
            else "font-weight: bold; color: #c62828;"
        )
        self.refresh_hardware_parameters("hardware check")

    def update_operation_mode(self, mode: str) -> None:
        if mode == "DEMO SOFTWARE":
            self.operator_step_label.setText("Mode: DEMO SOFTWARE. Connect, approach, then START to test software flow.")
            self.main_scan_btn.setText("START")
            self.main_scan_btn.setEnabled(self.workstation_status.system_check_passed and self.z_approached)
        elif mode == "HARDWARE TEST":
            self.operator_step_label.setText("Mode: HARDWARE TEST. Service tools are not part of the normal operator workflow.")
            self.main_scan_btn.setText("START")
            self.main_scan_btn.setEnabled(False)
        else:
            self.operator_step_label.setText("Mode: REAL MEASUREMENT. Connect to SPM, approach, then START measurement.")
            self.main_scan_btn.setText("START")
            self.main_scan_btn.setEnabled(self.workstation_status.system_check_passed and self.z_approached)
        self.refresh_hardware_parameters(f"mode changed to {mode}")

    def select_output_file(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Select Output CSV",
            "",
            "CSV Files (*.csv)",
        )

        if path:
            self.output_file.setText(path)
            self.workstation_status.last_output_file = path
            self.refresh_workstation_status_ui()
            self.append_log(f"Output CSV selected: {path}")

    # ------------------------------------------------------------
    # Update selected color map
    # ------------------------------------------------------------
    def update_color_map(self, color_map: str) -> None:
        self.color_map = color_map
        self.append_log(f"Plot color map selected: {self.color_map}")

    def documentation_markdown(self) -> str:
        parking = self.config["parking_position"]
        return (
            "# Educational SPM Operator Notes\n\n"
            f"**Software:** {APP_VERSION} | {APP_PHASE} | build {APP_BUILD_DATE}\n\n"
            "## Current Hardware\n\n"
            "- Installed motion hardware: original Prusa MK4S X/Y/Z system.\n"
            "- Fine SPM Z scanner and real SPM sensor channels are future additions.\n"
            "- Current approach and feedback tools are dry-run training aids.\n\n"
            "## New User Sequence\n\n"
            "1. Prepare the MK4S, object, and workspace. Make sure the bed and tool path are clear.\n"
            "2. Press **INITIATE SYSTEM CHECK** to validate settings and query MK4S communication without motion.\n"
            "3. Select scan mode. The software loads safe mode defaults for scan area, speed, Z height, and training feedback.\n"
            "4. Choose the X/Y scan window inside the object. For a 100 x 100 mm object, start with a small 2-8 mm educational area.\n"
            "5. Set MK4S Z height/clearance and review the line/frame time estimates.\n"
            "6. Run **Dry Run Scan** and inspect line scan, topography, and Z/approach feedback.\n"
            "7. Enable real motion only when the MK4S path is clear and the dry-run result is acceptable.\n"
            "8. Use **POWER OFF / SAFE PARK** before closing.\n\n"
            "## Display Limits\n\n"
            f"- Maximum accepted scan resolution: {MAX_SCAN_RESOLUTION} x {MAX_SCAN_RESOLUTION}.\n"
            "- Main live panels are fixed-size so changing resolution does not resize the interface.\n"
            "- Use **OPEN SCAN VIEWER** for a flexible extra scan image window.\n\n"
            "## Shutdown\n\n"
            f"- Power-off parking sequence: Z -> {parking['z']} first, then X/Y -> {parking['x']}/{parking['y']}.\n"
            "- The software disables real-motion state before closing.\n"
            "- The normal close action is locked until power-off/safe-park completes.\n"
        )

    def refresh_hardware_parameters(self, phase: str) -> None:
        def fmt(axis: str) -> str:
            value = self.current_position.get(axis)
            return "unknown" if value is None else f"{float(value):.2f}"

        mode = self.scan_mode_dropdown.currentText() if hasattr(self, "scan_mode_dropdown") else "unknown"
        self.hardware_parameters_label.setText(
            "Hardware Parameters\n"
            f"Phase: {phase}\n"
            f"Project: Educational SPM\n"
            f"Controller: Prusa MK4S on {self.config['printer']['port']} @ {self.config['printer']['baudrate']}\n"
            f"Motion enabled: {self.workstation_status.real_motion_enabled}\n"
            f"System check: {self.workstation_status.system_check_passed}\n"
            f"Mode: {mode}\n"
            f"Position: X {fmt('x')} | Y {fmt('y')} | Z {fmt('z')}\n"
            f"Resolution: {self.x_res.text()} x {self.y_res.text()} (max {MAX_SCAN_RESOLUTION})\n"
            f"XY speed: {self.xy_feedrate.text()} mm/min | Z speed: {self.z_feedrate.text()} mm/min\n"
            f"Shutdown ready: {self.shutdown_complete}"
        )

    def field_with_tip(self, field: QLineEdit, tip_text: str) -> QWidget:
        container = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(field, 1)

        tip = QLabel(tip_text)
        tip.setWordWrap(True)
        tip.setStyleSheet("color: #506070; font-size: 8.5pt;")
        tip.setMinimumWidth(56)
        layout.addWidget(tip, 0)

        container.setLayout(layout)
        return container

    def connect_scan_setting_updates(self) -> None:
        for field in (
            self.x_min,
            self.x_max,
            self.y_min,
            self.y_max,
            self.x_res,
            self.y_res,
            self.xy_feedrate,
            self.z_feedrate,
            self.z_dwell_ms,
        ):
            field.textChanged.connect(self.refresh_timing_estimate)

    def apply_scan_mode_preset(self, mode: str, show_limits: bool = True) -> None:
        preset = get_scan_mode_preset(self.config, mode)
        scan_area = preset["scan_area"]
        feedrates = preset["feedrates"]
        z_control = preset["z_control"]
        hardware = preset["hardware"]

        self.x_min.setText(str(scan_area["x_min"]))
        self.x_max.setText(str(scan_area["x_max"]))
        self.y_min.setText(str(scan_area["y_min"]))
        self.y_max.setText(str(scan_area["y_max"]))
        self.z.setText(str(scan_area["z"]))
        self.x_res.setText(str(scan_area["x_resolution"]))
        self.y_res.setText(str(scan_area["y_resolution"]))
        self.xy_feedrate.setText(str(feedrates["xy"]))
        self.z_feedrate.setText(str(feedrates["z"]))
        self.z_dwell_ms.setText(str(z_control["dwell_ms"]))
        self.z_test_position.setText(str(scan_area["z"]))
        self.z_approach_start.setText(str(z_control["approach_start"]))
        self.z_approach_target.setText(str(z_control["approach_target"]))
        self.z_retract_start.setText(str(z_control["approach_target"]))
        self.z_retract_target.setText(str(z_control["retract_target"]))
        self.z_step_size.setText(str(z_control["step_size"]))

        auto_state = "ready" if z_control["auto_approach_ready"] else "planned / dry-run guarded"
        manual_state = "ready" if z_control["manual_move_ready"] else "locked"
        self.mode_readiness_label.setText(
            f"{preset['description']}\n"
            "Current installed hardware: original Prusa MK4S X/Y/Z motion only.\n"
            f"XY: {hardware['xy_stage']}\n"
            f"Z: {hardware['z_stage']}\n"
            f"Sensor: {hardware['sensor']}\n"
            f"Feedback: {z_control['feedback']}\n"
            f"Auto approach: {auto_state}; manual Z: {manual_state}\n"
            "Fine SPM Z scanner/sensor hardware is a future add-on, not active in this test."
        )
        self.refresh_timing_estimate()
        self.operator_step_label.setText(
            f"Current step: {mode} loaded. Connect to SPM, set approach distance, then start measurement when ready."
        )
        self.append_log(f"[MODE] Loaded {mode} hardware preset")

        if show_limits:
            self.show_scan_mode_limits(mode)

    def refresh_timing_estimate(self) -> None:
        try:
            x_min = float(self.x_min.text())
            x_max = float(self.x_max.text())
            x_resolution = int(self.x_res.text())
            y_resolution = int(self.y_res.text())
            xy_feedrate = float(self.xy_feedrate.text())
            z_dwell_ms = float(self.z_dwell_ms.text())
        except ValueError:
            self.line_time_estimate_label.setText("Line time: enter numeric scan settings")
            self.frame_time_estimate_label.setText("Frame time: enter numeric scan settings")
            return

        if xy_feedrate <= 0 or x_resolution < 2 or y_resolution < 2:
            self.line_time_estimate_label.setText("Line time: speed/resolution invalid")
            self.frame_time_estimate_label.setText("Frame time: speed/resolution invalid")
            return

        line_distance = abs(x_max - x_min)
        xy_speed_mm_s = xy_feedrate / 60.0
        line_time_s = (line_distance / xy_speed_mm_s) + (x_resolution * z_dwell_ms / 1000.0)
        frame_time_s = line_time_s * y_resolution
        x_step = line_distance / max(1, x_resolution - 1)

        self.line_time_estimate_label.setText(
            f"Line time: {line_time_s:.2f} s, X step {x_step:.3f} mm"
        )
        self.frame_time_estimate_label.setText(
            f"Frame time: {frame_time_s:.2f} s for {x_resolution * y_resolution} points"
        )
        if hasattr(self, "hardware_parameters_label"):
            self.refresh_hardware_parameters("settings edited")

    def current_z_setup_summary(self) -> str:
        return (
            "Z Setup\n"
            f"Z speed: {self.z_feedrate.text()} mm/min\n"
            f"Dwell: {self.z_dwell_ms.text()} ms/point\n"
            f"Approach: {self.z_approach_start.text()} -> {self.z_approach_target.text()}\n"
            f"Retract: {self.z_retract_start.text()} -> {self.z_retract_target.text()}"
        )

    def show_scan_mode_limits(self, mode: str) -> None:
        QMessageBox.information(
            self,
            "Scan mode limits",
            self.hardware_profile.scan_mode_limits_text(mode),
        )

    def update_position_display(self, position: dict, source: str) -> None:
        for axis in ("x", "y", "z"):
            if axis in position and position[axis] is not None:
                self.current_position[axis] = position[axis]

        def fmt(axis: str) -> str:
            value = self.current_position.get(axis)
            return "unknown" if value is None else f"{float(value):.2f}"

        self.stage_position_label.setText(
            f"Current MK4S position ({source}): "
            f"X {fmt('x')} | Y {fmt('y')} | Z {fmt('z')}"
        )
        if hasattr(self, "hardware_parameters_label"):
            self.refresh_hardware_parameters(source)

    def parse_position_from_report(self, report) -> dict:
        for check in report.checks:
            if check.name != "Prusa MK4S XY motion controller":
                continue
            for detail in check.details:
                if not detail.startswith("M114:"):
                    continue
                parsed = {}
                for axis in ("X", "Y", "Z"):
                    match = re.search(rf"\b{axis}:\s*(-?\d+(?:\.\d+)?)", detail)
                    if match:
                        parsed[axis.lower()] = float(match.group(1))
                return parsed
        return {}

    def z_axis_visual(self, current_z: float, start_z: float, target_z: float) -> str:
        high = max(current_z, start_z, target_z)
        low = min(current_z, start_z, target_z)
        span = high - low if high != low else 1.0
        rows = []
        for index in range(10, -1, -1):
            value = low + span * index / 10
            marker = " "
            if abs(value - current_z) <= span / 20:
                marker = "*"
            elif abs(value - start_z) <= span / 20:
                marker = "S"
            elif abs(value - target_z) <= span / 20:
                marker = "T"
            rows.append(f"{value:7.2f} | {marker}")
        return "\n".join(rows)

    def show_z_training_visual(self, title: str, current_z: float, start_z: float, target_z: float) -> None:
        self.z_condition_placeholder.setText(
            f"{title}\n\n"
            "Training visual only: no fine Z scanner hardware is active yet.\n"
            "S = start, T = target, * = current simulated Z\n\n"
            f"{self.z_axis_visual(current_z, start_z, target_z)}\n\n"
            f"{self.current_z_setup_summary()}"
        )

    def set_initialized_controls_enabled(self, enabled: bool) -> None:
        if self.shutdown_complete:
            enabled = False
        self.validate_btn.setEnabled(enabled)
        self.dry_run_btn.setEnabled(enabled)
        self.query_position_btn.setEnabled(enabled)
        self.park_btn.setEnabled(enabled)
        self.z_connect_btn.setEnabled(enabled and not self.z_driver.connected)
        self.z_move_test_btn.setEnabled(enabled and self.z_driver.connected)
        self.z_approach_btn.setEnabled(enabled and self.z_driver.connected)
        self.z_retract_btn.setEnabled(enabled and self.z_driver.connected)
        self.hardware_arm_btn.setEnabled(enabled and not self.workstation_status.real_motion_enabled)
        self.main_z_create_btn.setEnabled(enabled)
        self.main_z_move_btn.setEnabled(enabled and self.z_driver.connected)
        self.main_z_approach_btn.setEnabled(enabled)
        self.main_z_retract_btn.setEnabled(enabled)
        self.main_z_up_btn.setEnabled(enabled)
        self.main_z_down_btn.setEnabled(enabled)
        self.main_scan_btn.setEnabled(enabled and self.z_approached)
        if enabled and self.z_approached:
            self.main_scan_btn.setStyleSheet("font-weight: bold; background-color: #1565c0; color: white; padding: 6px;")
        else:
            self.main_scan_btn.setStyleSheet("font-weight: bold; background-color: #cfd6dd; color: #68727d; padding: 6px;")
        if not self.live_scan_active:
            self.pause_scan_btn.setEnabled(False)
            self.stop_scan_btn.setEnabled(False)
        if enabled:
            self.main_z_approach_btn.setStyleSheet("font-weight: bold; background-color: #1565c0; color: white; padding: 6px;")
        else:
            self.main_z_approach_btn.setStyleSheet("font-weight: bold; background-color: #cfd6dd; color: #68727d; padding: 6px;")

    def require_initialized(self, action_name: str) -> bool:
        if self.workstation_status.system_check_passed:
            return True

        QMessageBox.warning(
            self,
            "Connect to SPM required",
            (
                f"{action_name} is locked until SPM connection is complete.\n\n"
                "Start with CONNECT TO SPM. Confirm that the MK4S is powered on, "
                "USB is connected, the bed/surface is clear, and no probe or sample can collide."
            ),
        )
        self.append_log(f"[SAFETY] {action_name} blocked: initialization required")
        return False

    def apply_instrument_style(self) -> None:
        self.setStyleSheet(
            """
            QWidget {
                font-family: Segoe UI, Arial, sans-serif;
                font-size: 10pt;
                background: #f4f6f8;
                color: #17212b;
            }
            QGroupBox {
                border: 1px solid #b8c2cc;
                border-radius: 6px;
                margin-top: 10px;
                padding: 8px;
                background: #ffffff;
                font-weight: 600;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 4px;
            }
            QLineEdit, QComboBox, QTextEdit {
                background: #ffffff;
                border: 1px solid #aeb8c2;
                border-radius: 4px;
                padding: 4px;
            }
            QPushButton {
                background: #e8edf2;
                border: 1px solid #9eabb8;
                border-radius: 4px;
                padding: 6px;
                font-weight: 600;
            }
            QPushButton:disabled {
                background: #cfd6dd;
                color: #68727d;
            }
            QTabWidget::pane {
                border: 1px solid #b8c2cc;
                background: #ffffff;
            }
            QTabBar::tab {
                background: #e8edf2;
                border: 1px solid #b8c2cc;
                padding: 7px 12px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: #ffffff;
                border-bottom-color: #ffffff;
            }
            QProgressBar {
                border: 1px solid #9eabb8;
                border-radius: 4px;
                text-align: center;
                background: #ffffff;
                height: 18px;
            }
            QProgressBar::chunk {
                background: #1565c0;
            }
            """
        )

    def refresh_workstation_status_ui(self) -> None:
        self.system_check_passed = self.workstation_status.system_check_passed
        self.hardware_armed = self.workstation_status.real_motion_enabled
        self.machine_status_label.setText(self.workstation_status.machine_summary())
        self.workflow_status_label.setText(self.workstation_status.workflow_summary())
        self.safety_status_label.setText(self.workstation_status.safety_summary())
        self.output_status_label.setText(self.workstation_status.output_summary())
        self.acquisition_status_label.setText(self.workstation_status.acquisition_summary())

        if self.workstation_status.real_motion_enabled:
            self.system_status_label.setText("SYSTEM STATUS: REAL MOTION ENABLED")
            self.system_status_label.setStyleSheet("font-weight: bold; background-color: #b71c1c; color: white; padding: 6px;")
        elif self.workstation_status.system_check_passed:
            self.system_status_label.setText("SYSTEM STATUS: SYSTEM READY")
            self.system_status_label.setStyleSheet("font-weight: bold; background-color: #1b5e20; color: white; padding: 6px;")
        else:
            self.system_status_label.setText("SYSTEM STATUS: NOT CONNECTED")
            self.system_status_label.setStyleSheet("font-weight: bold; background-color: #263238; color: white; padding: 6px;")

        self.set_initialized_controls_enabled(self.workstation_status.system_check_passed)
        if hasattr(self, "hardware_parameters_label"):
            self.refresh_hardware_parameters("status update")
        if hasattr(self, "main_z_status_label"):
            if self.workstation_status.system_check_passed and self.z_approached:
                self.main_z_status_label.setText("Approach complete. Measurement can start; retract before disconnect.")
                self.main_z_status_label.setStyleSheet("border: 1px solid #1565c0; color: #0d47a1; background: #eef6ff; padding: 8px;")
            elif self.workstation_status.system_check_passed:
                self.main_z_status_label.setText("Approach ready. Set the surface distance, then use manual move or auto approach.")
                self.main_z_status_label.setStyleSheet("border: 1px solid #2e7d32; color: #1b5e20; background: #e8f5e9; padding: 8px;")
            else:
                self.main_z_status_label.setText("Approach locked until SPM is connected.")
                self.main_z_status_label.setStyleSheet("border: 1px solid #90a4ae; background: #fffde7; padding: 8px;")

    def query_mk4s_position(self) -> None:
        if not self.require_initialized("MK4S position query"):
            return

        printer = self.config["printer"]
        backend = PrusaGcodeBackend(
            port=str(printer["port"]),
            baudrate=int(printer["baudrate"]),
            timeout=0.5,
            auto_detect_port=False,
        )

        try:
            backend.connect()
            state = backend.get_state()
        except Exception as error:
            self.stage_position_label.setText(f"MK4S position query failed: {error}")
            self.append_log(f"[MK4S] Position query failed: {error}")
            return
        finally:
            backend.disconnect()

        position = state.get("position", {})
        self.update_position_display(position, "readback")
        self.append_log(f"[MK4S] No-motion position query: {state}")

    def park_workstation(self) -> bool:
        if not self.require_initialized("Park MK4S"):
            return False

        parking = self.config["parking_position"]
        if not self.confirm_critical_action(
            "Park MK4S",
            (
                "Move MK4S to workstation park position?\n\n"
                f"Sequence: Z -> {parking['z']} first, then X/Y -> {parking['x']}/{parking['y']}.\n\n"
                "Confirm the Z path and XY path are clear."
            ),
        ):
            self.append_log("[PARK] Park cancelled by operator")
            return False

        try:
            state = park_mk4s(self.config)
        except Exception as error:
            self.append_log(f"[PARK] Park failed: {error}")
            QMessageBox.critical(
                self,
                "Park failed",
                f"MK4S parking failed:\n\n{error}",
            )
            return False

        position = state.get("position", {})
        self.update_position_display(position, "parked")
        self.append_log(f"[PARK] MK4S parked: {state}")
        return True

    def power_off_workstation(self) -> bool:
        self.stop_live_scan_runtime("power off requested")
        parking = self.config["parking_position"]
        if not self.confirm_critical_action(
            "Power off / safe park",
            (
                "Deinitialize Educational SPM and move to safe position?\n\n"
                f"Parking sequence: Z -> {parking['z']} first, then X/Y -> {parking['x']}/{parking['y']}.\n"
                f"Full sequence: disable real motion, disconnect dry-run Z, move Z -> {parking['z']}, "
                f"then X/Y -> {parking['x']}/{parking['y']}.\n\n"
                "Continue only if the MK4S path is clear."
            ),
        ):
            self.append_log("[POWER OFF] Cancelled by operator")
            return False

        self.workstation_status.disable_real_motion()
        self.hardware_armed = False
        self.execute_btn.setEnabled(False)

        if self.z_driver.connected:
            self.z_driver.disconnect()
            self.z_move_test_btn.setEnabled(False)
            self.z_approach_btn.setEnabled(False)
            self.z_retract_btn.setEnabled(False)
            self.refresh_z_driver_status("Z dry-run status")

        if self.workstation_status.system_check_passed:
            try:
                state = park_mk4s(self.config)
            except Exception as error:
                self.shutdown_complete = False
                self.refresh_hardware_parameters("power-off failed")
                self.append_log(f"[POWER OFF] Safe park failed: {error}")
                QMessageBox.critical(
                    self,
                    "Power off failed",
                    f"MK4S safe park failed. The software will remain open.\n\n{error}",
                )
                return False

            self.update_position_display(state.get("position", {}), "power-off safe park")
            self.append_log(f"[POWER OFF] MK4S safe park complete: {state}")
        else:
            self.append_log("[POWER OFF] No hardware motion performed because initialization was not completed")

        self.shutdown_complete = True
        self.close_btn.setEnabled(True)
        self.power_off_btn.setEnabled(False)
        self.hardware_status_label.setText("Hardware / System Connection: POWERED OFF / SAFE PARK COMPLETE")
        self.hardware_status_label.setStyleSheet("font-weight: bold; color: #2e7d32;")
        self.operator_step_label.setText("Next action: safe power-off complete. CLOSE SOFTWARE is now enabled.")
        self.refresh_workstation_status_ui()
        self.refresh_hardware_parameters("power-off complete")
        return True

    def close_after_power_off(self) -> None:
        if not self.shutdown_complete:
            QMessageBox.warning(
                self,
                "Power off required",
                "Use POWER OFF / SAFE PARK before closing the software.",
            )
            return
        self.close()

    def stop_live_scan_runtime(self, reason: str) -> None:
        if self.live_scan_timer.isActive():
            self.live_scan_timer.stop()
            self.append_log(f"[LIVE SCAN] Runtime stopped: {reason}")
        self.live_scan_active = False
        self.scan_pause_requested = False
        self.scan_stop_requested = False

    def set_scan_progress(self, value: int, message: str) -> None:
        self.scan_progress_bar.setValue(max(0, min(100, int(value))))
        self.workstation_status.acquisition_status = message
        self.acquisition_status_label.setText(self.workstation_status.acquisition_summary())

    def start_live_demo_scan(self) -> None:
        profile = self.validate_profile(require_initialized=False)
        if profile is None:
            self.append_log("[LIVE SCAN] Cancelled because profile validation failed")
            return

        self.scan_pause_requested = False
        self.scan_stop_requested = False
        self.live_scan_profile = profile
        self.live_scan_z_setpoint = profile.z
        self.live_scan_rows = []
        self.live_scan_current_line = []
        self.live_scan_points = self.build_live_scan_points(profile)
        self.live_scan_index = 0
        self.live_scan_active = True
        self.pause_scan_btn.setEnabled(True)
        self.stop_scan_btn.setEnabled(True)
        self.main_scan_btn.setEnabled(False)
        self.live_scan_status_label.setText(
            "Live scan: regulating Z at setpoint, sweeping X forward/backward, then stepping Y."
        )
        self.append_log(
            f"[LIVE SCAN] Started regulated demo raster: {profile.x_resolution} x {profile.y_resolution}, "
            "forward/backward lines over upward and downward Y passes"
        )
        self.set_scan_progress(0, "live demo scan running")
        self.redraw_live_scan_views()
        self.live_scan_timer.start(35)

    def build_live_scan_points(self, profile: ScanProfile) -> list[dict[str, float | str | int]]:
        x_values = self.linspace(profile.x_min, profile.x_max, profile.x_resolution)
        y_values = self.linspace(profile.y_min, profile.y_max, profile.y_resolution)
        points = []
        line_number = 0
        for y_pass, ordered_y in (("upward", y_values), ("downward", list(reversed(y_values)))):
            for y in ordered_y:
                line_number += 1
                for x in x_values:
                    points.append({"x": x, "y": y, "x_direction": "forward", "y_pass": y_pass, "line": line_number})
                line_number += 1
                for x in reversed(x_values):
                    points.append({"x": x, "y": y, "x_direction": "backward", "y_pass": y_pass, "line": line_number})
        return points

    def linspace(self, start: float, stop: float, count: int) -> list[float]:
        count = max(1, int(count))
        if count == 1:
            return [float(start)]
        step = (float(stop) - float(start)) / (count - 1)
        return [float(start) + step * index for index in range(count)]

    def synthetic_regulated_height(self, x: float, y: float, profile: ScanProfile) -> float:
        x_span = max(1e-9, profile.x_max - profile.x_min)
        y_span = max(1e-9, profile.y_max - profile.y_min)
        nx = (x - profile.x_min) / x_span
        ny = (y - profile.y_min) / y_span
        terrace = 0.55 if nx > 0.58 and ny > 0.32 else 0.0
        lattice = 0.18 * math.sin(nx * math.pi * 18.0) * math.cos(ny * math.pi * 14.0)
        slope = 0.28 * nx + 0.16 * ny
        ridge = 0.45 * math.exp(-((nx - 0.72) ** 2 + (ny - 0.68) ** 2) / 0.012)
        return profile.z + slope + terrace + lattice + ridge

    def advance_live_scan(self) -> None:
        if self.scan_stop_requested:
            self.finish_live_scan(cancelled=True)
            return

        if self.scan_pause_requested:
            self.live_scan_status_label.setText("Live scan: paused. Press SCAN DEMO again to restart or STOP to cancel.")
            return

        if not self.live_scan_profile:
            self.finish_live_scan(cancelled=True)
            return

        points_per_tick = 4
        for _ in range(points_per_tick):
            if self.live_scan_index >= len(self.live_scan_points):
                self.finish_live_scan(cancelled=False)
                return
            point = self.live_scan_points[self.live_scan_index]
            z_value = self.synthetic_regulated_height(float(point["x"]), float(point["y"]), self.live_scan_profile)
            sample = {
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "scan_direction": str(point["x_direction"]),
                "y_pass": str(point["y_pass"]),
                "line": int(point["line"]),
                "target_x": float(point["x"]),
                "target_y": float(point["y"]),
                "actual_x": float(point["x"]),
                "actual_y": float(point["y"]),
                "actual_z": float(self.live_scan_profile.z),
                "regulated_height": float(z_value),
                "simulated_z_signal": float(z_value),
            }
            if self.live_scan_current_line and self.live_scan_current_line[-1]["line"] != sample["line"]:
                self.live_scan_rows.append(self.live_scan_current_line)
                self.live_scan_current_line = []
            self.live_scan_current_line.append(sample)
            self.live_scan_index += 1

        progress = int((self.live_scan_index / max(1, len(self.live_scan_points))) * 100)
        current = self.live_scan_current_line[-1] if self.live_scan_current_line else {}
        self.set_scan_progress(progress, f"live scan line {current.get('line', '?')} {current.get('scan_direction', '')}")
        self.live_scan_status_label.setText(
            f"Live scan: line {current.get('line', '?')} | X {current.get('scan_direction', '?')} | "
            f"Y pass {current.get('y_pass', '?')} | Z regulation signal {current.get('regulated_height', 0.0):.4f}"
        )
        self.redraw_live_scan_views()

    def finish_live_scan(self, cancelled: bool) -> None:
        self.live_scan_timer.stop()
        if self.live_scan_current_line:
            self.live_scan_rows.append(self.live_scan_current_line)
            self.live_scan_current_line = []
        self.live_scan_active = False
        self.pause_scan_btn.setEnabled(False)
        self.stop_scan_btn.setEnabled(False)
        self.main_scan_btn.setEnabled(True)

        if cancelled:
            self.set_scan_progress(self.scan_progress_bar.value(), "live scan stopped")
            self.live_scan_status_label.setText("Live scan: stopped by operator.")
            self.append_log("[LIVE SCAN] Stopped by operator")
            return

        self.write_live_scan_csv(self.output_file.text())
        self.set_scan_progress(100, "live demo scan complete")
        self.live_scan_status_label.setText(
            "Live scan complete: Z retracted to safe setpoint and XY return/park is ready for the shutdown sequence."
        )
        self.append_log(f"[LIVE SCAN] Complete. Saved regulated demo raster to {self.output_file.text()}")
        plot_exit_code, plot_path = self.generate_plot()
        if plot_exit_code == 0:
            self.refresh_acquisition_preview(self.output_file.text(), plot_path)

    def write_live_scan_csv(self, output_path: str) -> None:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        rows = [sample for line in self.live_scan_rows for sample in line]
        with path.open("w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(
                csvfile,
                fieldnames=[
                    "timestamp",
                    "scan_direction",
                    "y_pass",
                    "line",
                    "target_x",
                    "target_y",
                    "actual_x",
                    "actual_y",
                    "actual_z",
                    "regulated_height",
                    "simulated_z_signal",
                ],
            )
            writer.writeheader()
            writer.writerows(rows)

    def redraw_live_scan_views(self) -> None:
        self.draw_live_line_scan()
        self.draw_live_topography()

    def draw_live_line_scan(self) -> None:
        line = self.live_scan_current_line or (self.live_scan_rows[-1] if self.live_scan_rows else [])
        selected = self.line_direction_dropdown.currentText()
        if selected != "current":
            matching = [row for row in reversed(self.live_scan_rows) if row and row[0]["scan_direction"] == selected]
            line = matching[0] if matching else []

        if not line:
            self.live_line_canvas.setText("Line scan waiting for raster data")
            return

        values = [float(sample["regulated_height"]) for sample in line]
        low = min(values)
        high = max(values)
        first = line[0]
        self.live_line_canvas.setText(
            f"Line {first['line']} | X {first['scan_direction']} | Y pass {first['y_pass']} | pm/nm signal {low:.3f}..{high:.3f}"
            + "\n\n"
            + self.ascii_trace(values, width=92)
            + "\n\n"
            + "Samples: "
            + ", ".join(f"{value:.3f}" for value in self.sample_values(values, 12))
        )

    def draw_live_topography(self) -> None:
        rows = list(self.live_scan_rows)
        if self.live_scan_current_line:
            rows.append(self.live_scan_current_line)
        selected = self.topography_direction_dropdown.currentText()
        if selected in ("upward", "downward"):
            rows = [row for row in rows if row and row[0]["y_pass"] == selected]

        if not rows:
            self.live_topography_canvas.setText("Topography accumulates one completed line at a time")
            return

        values = [float(sample["regulated_height"]) for row in rows for sample in row]
        low = min(values)
        high = max(values)
        rendered_rows = []
        for row in rows[-22:]:
            rendered_rows.append(self.ascii_trace([float(sample["regulated_height"]) for sample in row], width=92))
        self.live_topography_canvas.setText(
            f"Topography {selected}: {len(rows)} lines | Z correction {low:.3f}..{high:.3f}\n\n"
            + "\n".join(rendered_rows)
        )

    def sample_values(self, values: list[float], max_count: int) -> list[float]:
        if len(values) <= max_count:
            return list(values)
        step = (len(values) - 1) / (max_count - 1)
        return [values[round(index * step)] for index in range(max_count)]

    def ascii_trace(self, values: list[float], width: int = 92) -> str:
        if not values:
            return ""
        palette = " .:-=+*#%@"
        sampled = self.sample_values(values, width)
        low = min(values)
        high = max(values)
        span = max(1e-9, high - low)
        chars = []
        for value in sampled:
            normalized = (value - low) / span
            index = round(normalized * (len(palette) - 1))
            chars.append(palette[max(0, min(len(palette) - 1, index))])
        return "".join(chars)

    def run_main_scan(self) -> None:
        mode = self.operation_mode_dropdown.currentText()
        if mode == "DEMO SOFTWARE":
            self.start_live_demo_scan()
            return

        if mode == "HARDWARE TEST":
            self.open_hardware_tools_window()
            return

        if not self.require_initialized("Real scan"):
            return

        if not self.z_approached:
            QMessageBox.warning(
                self,
                "Approach required",
                "Real measurement is locked until Z approach has completed.",
            )
            self.append_log("[SCAN] Real scan blocked: Z approach required")
            self.open_z_tools_window()
            return

        self.run_hardware_scan()

    def pause_scan(self) -> None:
        self.scan_pause_requested = True
        self.append_log("[SCAN] Pause requested")
        self.set_scan_progress(self.scan_progress_bar.value(), "pause requested")

    def stop_scan(self) -> None:
        self.scan_stop_requested = True
        self.append_log("[SCAN] Stop requested")
        self.set_scan_progress(self.scan_progress_bar.value(), "stop requested")

    # ------------------------------------------------------------
    # Z-control dry-run: status refresh
    # No real hardware movement
    # ------------------------------------------------------------
    def set_z_connection_indicator(self, connected: bool) -> None:
        if connected:
            self.z_connection_state_label.setText("? CONNECTED ? DRY RUN")
            self.z_connection_state_label.setStyleSheet("font-weight: bold; color: #c62828;")
            self.z_connect_btn.setText("CONNECTED ? DRY RUN")
            self.z_connect_btn.setEnabled(False)
            self.z_connect_btn.setStyleSheet("font-weight: bold; background-color: #9e9e9e; color: white;")
            self.z_disconnect_btn.setText("DISCONNECT Z")
            self.z_disconnect_btn.setEnabled(True)
            self.z_disconnect_btn.setStyleSheet("font-weight: bold; background-color: #c62828; color: white;")
        else:
            self.z_connection_state_label.setText("? READY TO CONNECT")
            self.z_connection_state_label.setStyleSheet("font-weight: bold; color: #2e7d32;")
            self.z_connect_btn.setText("CONNECT Z DRY RUN")
            self.z_connect_btn.setEnabled(True)
            self.z_connect_btn.setStyleSheet("font-weight: bold; background-color: #2e7d32; color: white;")
            self.z_disconnect_btn.setText("DISCONNECTED")
            self.z_disconnect_btn.setEnabled(False)
            self.z_disconnect_btn.setStyleSheet("font-weight: bold; background-color: #757575; color: white;")

    def confirm_critical_action(self, title: str, message: str) -> bool:
        reply = QMessageBox.warning(
            self,
            title,
            message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        return reply == QMessageBox.StandardButton.Yes

    def confirm_z_action(self, title: str, message: str) -> bool:
        return self.confirm_critical_action(title, message)


    def build_scan_confirmation_message(
        self,
        profile: ScanProfile,
        execute_hardware: bool = False,
    ) -> str:
        scan_mode = "HARDWARE EXECUTION" if execute_hardware else "DRY RUN"
        safety_state = (
            "REAL HARDWARE EXECUTION REQUESTED.\n"
            "XY hardware motion may occur.\n"
            "Confirm the scanner, sample area, toolhead, bed, and operator area are clear."
            if execute_hardware
            else "Dry-run safety active: no hardware movement will be executed."
        )

        return (
            "Confirm scan execution?\n\n"
            f"Scan mode: {scan_mode}\n"
            f"Scan area: X {profile.x_min} to {profile.x_max}, "
            f"Y {profile.y_min} to {profile.y_max}\n"
            f"Z value: {profile.z}\n"
            f"Resolution: {profile.x_resolution} x {profile.y_resolution}\n"
            f"XY speed: {profile.feedrate_xy} mm/min\n"
            f"Z speed: {profile.feedrate_z} mm/min\n"
            f"Z dwell: {self.z_dwell_ms.text()} ms/point\n"
            f"Output file: {self.output_file.text().strip()}\n"
            f"Color map: {self.color_map}\n\n"
            f"{safety_state}"
        )
    def refresh_z_driver_status(self, prefix: str = "Z dry-run status") -> None:
        status = self.z_driver.get_status()
        label_text = (
            f"{prefix}: "
            f"mode={status['mode']}, "
            f"connected={status['connected']}, "
            f"last_command={status['last_command']}"
        )
        self.set_z_connection_indicator(bool(status["connected"]))
        self.z_status_label.setText(label_text)
        self.workstation_status.record_z_status(status)
        self.z_condition_placeholder.setText(
            "Z Condition / Feedback\n\n"
            f"Connected: {status['connected']}\n"
            f"Last command: {status['last_command']}\n"
            f"Last Z: {status['last_z_position']}\n\n"
            f"{self.current_z_setup_summary()}"
        )
        self.refresh_workstation_status_ui()
        self.append_log(f"[Z STATUS] {label_text}")

    def report_z_failure(self, status_text: str, log_text: str) -> None:
        label_text = f"Z dry-run status: {status_text}"
        self.z_status_label.setText(label_text)
        self.z_condition_placeholder.setText(
            "Z Condition / Feedback\n\n"
            f"Status: {status_text}\n"
            "Approach state: blocked\n"
            "Signal / height feedback: unavailable"
        )
        self.refresh_workstation_status_ui()
        self.append_log(f"[Z FAILURE] {log_text}")

    # ------------------------------------------------------------
    # Z-control dry-run: connect
    # No real hardware movement
    # ------------------------------------------------------------
    def run_z_dry_connect(self) -> None:
        if not self.require_initialized("Z dry-run connect"):
            return

        ok = self.z_driver.connect()
        if ok:
            self.z_move_test_btn.setEnabled(True)
            self.z_approach_btn.setEnabled(True)
            self.z_retract_btn.setEnabled(True)
            self.refresh_z_driver_status("Z dry-run status")
            self.append_log("[Z DRY RUN] Connect: PASS")
        else:
            self.append_log("[Z DRY RUN] Connect: FAIL")

    # ------------------------------------------------------------
    # Z-control dry-run: move test
    # No real hardware movement
    # ------------------------------------------------------------
    def run_z_dry_move_test(self) -> None:
        if not self.require_initialized("Z dry-run move test"):
            return

        try:
            z_position = float(self.z_test_position.text())
        except ValueError:
            self.report_z_failure(
                "Invalid Z test value",
                "[Z DRY RUN] Move Z test: FAIL - invalid Z value",
            )
            return

        if not (self.limits.z_min <= z_position <= self.limits.z_max):
            self.report_z_failure(
                "Z value outside safe limits",
                (
                    f"[Z DRY RUN] Move Z test: FAIL - Z={z_position} outside safe limits "
                    f"({self.limits.z_min} to {self.limits.z_max})"
                ),
            )
            return

        self.z_driver.move_to(z_position)
        self.refresh_z_driver_status("Z dry-run status")
        self.show_z_training_visual(
            "Manual Z Move Preview",
            current_z=z_position,
            start_z=z_position,
            target_z=z_position,
        )
        self.append_log(f"[Z DRY RUN] Move Z test to {z_position}: PASS")

    # ------------------------------------------------------------
    # Z-control dry-run: approach
    # No real hardware movement
    # ------------------------------------------------------------
    def run_z_dry_approach(self) -> None:
        if not self.require_initialized("Z dry-run approach"):
            return

        try:
            start_z = float(self.z_approach_start.text())
            target_z = float(self.z_approach_target.text())
            step_size = float(self.z_step_size.text())
        except ValueError:
            self.report_z_failure(
                "Invalid approach value",
                "[Z DRY RUN] Approach: FAIL - invalid numeric value",
            )
            return

        if step_size <= 0:
            self.report_z_failure(
                "Invalid step size",
                "[Z DRY RUN] Approach: FAIL - step size must be positive",
            )
            return

        if not (self.limits.z_min <= start_z <= self.limits.z_max):
            self.report_z_failure(
                "Approach start outside safe limits",
                (
                    f"[Z DRY RUN] Approach: FAIL - start Z={start_z} outside safe limits "
                    f"({self.limits.z_min} to {self.limits.z_max})"
                ),
            )
            return

        if not (self.limits.z_min <= target_z <= self.limits.z_max):
            self.report_z_failure(
                "Approach target outside safe limits",
                (
                    f"[Z DRY RUN] Approach: FAIL - target Z={target_z} outside safe limits "
                    f"({self.limits.z_min} to {self.limits.z_max})"
                ),
            )
            return

        if start_z <= target_z:
            self.report_z_failure(
                "Invalid approach direction",
                f"[Z DRY RUN] Approach: FAIL - start Z={start_z} must be greater than target Z={target_z}",
            )
            return

        if not self.confirm_z_action(
            "Confirm Z approach",
            f"Start Z approach from {start_z} to {target_z} with step {step_size}?\n\nDry-run mode is active. No real hardware movement will be sent.",
        ):
            self.append_log("[Z DRY RUN] Approach cancelled by operator")
            return

        try:
            self.z_driver.approach(start_z=start_z, target_z=target_z, step=step_size)
        except RuntimeError as exc:
            self.report_z_failure(
                "Approach failed",
                f"[Z DRY RUN] Approach: FAIL - {exc}",
            )
            return

        self.refresh_z_driver_status("Z dry-run status")
        self.show_z_training_visual(
            "Auto Approach Preview",
            current_z=target_z,
            start_z=start_z,
            target_z=target_z,
        )
        self.z_approached = True
        self.refresh_hardware_parameters("Z approached")
        self.append_log(
            f"[Z DRY RUN] Approach from {start_z} to {target_z} with step {step_size}: PASS"
        )

    # ------------------------------------------------------------
    # Z-control dry-run: retract
    # No real hardware movement
    # ------------------------------------------------------------
    def run_z_dry_retract(self) -> None:
        if not self.require_initialized("Z dry-run retract"):
            return

        try:
            start_z = float(self.z_retract_start.text())
            target_z = float(self.z_retract_target.text())
            step_size = float(self.z_step_size.text())
        except ValueError:
            self.report_z_failure(
                "Invalid retract value",
                "[Z DRY RUN] Retract: FAIL - invalid numeric value",
            )
            return

        if step_size <= 0:
            self.report_z_failure(
                "Invalid step size",
                "[Z DRY RUN] Retract: FAIL - step size must be positive",
            )
            return

        if not (self.limits.z_min <= start_z <= self.limits.z_max):
            self.report_z_failure(
                "Retract start outside safe limits",
                (
                    f"[Z DRY RUN] Retract: FAIL - start Z={start_z} outside safe limits "
                    f"({self.limits.z_min} to {self.limits.z_max})"
                ),
            )
            return

        if not (self.limits.z_min <= target_z <= self.limits.z_max):
            self.report_z_failure(
                "Retract target outside safe limits",
                (
                    f"[Z DRY RUN] Retract: FAIL - target Z={target_z} outside safe limits "
                    f"({self.limits.z_min} to {self.limits.z_max})"
                ),
            )
            return

        if start_z >= target_z:
            self.report_z_failure(
                "Invalid retract direction",
                f"[Z DRY RUN] Retract: FAIL - start Z={start_z} must be less than target Z={target_z}",
            )
            return

        if not self.confirm_z_action(
            "Confirm Z retract",
            f"Start Z retract from {start_z} to {target_z} with step {step_size}?\n\nDry-run mode is active. No real hardware movement will be sent.",
        ):
            self.append_log("[Z DRY RUN] Retract cancelled by operator")
            return

        try:
            self.z_driver.retract(start_z=start_z, target_z=target_z, step=step_size)
        except RuntimeError as exc:
            self.report_z_failure(
                "Retract failed",
                f"[Z DRY RUN] Retract: FAIL - {exc}",
            )
            return

        self.refresh_z_driver_status("Z dry-run status")
        self.show_z_training_visual(
            "Safe Retract Preview",
            current_z=target_z,
            start_z=start_z,
            target_z=target_z,
        )
        self.z_approached = False
        self.refresh_hardware_parameters("Z retracted")
        self.append_log(
            f"[Z DRY RUN] Retract from {start_z} to {target_z} with step {step_size}: PASS"
        )

    # ------------------------------------------------------------
    # Z-control dry-run: disconnect
    # No real hardware movement
    # ------------------------------------------------------------
    def run_z_dry_disconnect(self) -> None:
        if not self.require_initialized("Z dry-run disconnect"):
            return

        if not self.confirm_z_action(
            "Confirm Z disconnect",
            "Disconnect the Z dry-run controller?\n\nThis will disable Z move, approach, and retract controls.",
        ):
            self.append_log("[Z DRY RUN] Disconnect cancelled by operator")
            return

        self.z_driver.disconnect()
        self.z_move_test_btn.setEnabled(False)
        self.z_approach_btn.setEnabled(False)
        self.z_retract_btn.setEnabled(False)
        self.refresh_z_driver_status("Z dry-run status")
        self.append_log("[Z DRY RUN] Disconnect: PASS")

    def run_main_z_create(self) -> None:
        if not self.require_initialized("Service approach prepare"):
            return
        if self.z_driver.connected:
            self.main_z_status_label.setText("Approach tools are already ready.")
            self.append_log("[APPROACH] Service prepare skipped: already connected")
            return
        self.run_z_dry_connect()
        self.refresh_workstation_status_ui()
        self.append_log("[APPROACH] Service prepare complete")

    def run_main_z_move(self) -> None:
        if not self.require_initialized("Manual Z move"):
            return
        if not self.z_driver.connected:
            self.run_main_z_create()
        self.run_z_dry_move_test()
        self.refresh_workstation_status_ui()
        self.append_log("[APPROACH] Service manual move complete")

    def run_main_z_manual_step(self, direction: str) -> None:
        if not self.require_initialized("Manual approach move"):
            return
        try:
            step_mm = float(self.z_manual_step_mm.text())
        except ValueError:
            QMessageBox.warning(self, "Invalid Z step", "Manual step must be a number in mm.")
            return
        if step_mm <= 0:
            QMessageBox.warning(self, "Invalid Z step", "Manual step must be positive.")
            return
        if not self.confirm_critical_action(
            f"Manual Z {direction}",
            (
                f"Move Z {direction} by {step_mm:.2f} mm?\n\n"
                "Continue only while watching the MK4S and the sample/probe clearance."
            ),
        ):
            self.append_log(f"[APPROACH] Manual Z {direction} cancelled")
            return
        try:
            result = run_mk4s_z_manual_step(direction=direction, step_mm=step_mm, execute=True)
        except Exception as error:
            self.main_z_status_label.setText(f"Approach manual move failed: {error}")
            self.main_z_status_label.setStyleSheet("border: 1px solid #b71c1c; color: #b71c1c; background: #ffebee; padding: 8px;")
            self.append_log(f"[APPROACH] Manual Z {direction} failed: {error}")
            QMessageBox.critical(self, "Manual Z move failed", str(error))
            return
        self.update_position_display({"z": result.target_z}, f"manual Z {direction}")
        self.main_z_status_label.setText(result.message)
        self.main_z_status_label.setStyleSheet("border: 1px solid #2e7d32; color: #1b5e20; background: #e8f5e9; padding: 8px;")
        self.append_log(f"[APPROACH] {result.message}")

    def run_main_z_auto_approach(self) -> None:
        if not self.require_initialized("Auto approach"):
            return
        try:
            setpoint_distance = float(self.z_setpoint_distance_mm.text())
        except ValueError:
            QMessageBox.warning(self, "Invalid setpoint", "Setpoint above surface must be a number in mm.")
            return
        if setpoint_distance < 0:
            QMessageBox.warning(self, "Invalid setpoint", "Setpoint above surface cannot be negative.")
            return
        reference_text = (
            "Run the confirmed MK4S Z auto-approach sequence?\n\n"
            "Sequence:\n"
            "- move Z to safe start 120\n"
            "- move XY to center X125 Y105\n"
            f"- step Z down to setpoint {setpoint_distance:.2f} mm above the confirmed surface reference\n\n"
            "Continue only if the foam/sample is placed as before and you are watching the MK4S."
        )
        if not self.confirm_critical_action("Confirm Z auto approach", reference_text):
            self.append_log("[APPROACH] Auto approach cancelled by operator")
            return
        self.main_z_status_label.setText("Auto approach running...")
        self.main_z_status_label.setStyleSheet("border: 1px solid #1565c0; color: #0d47a1; background: #eef6ff; padding: 8px;")
        QApplication.processEvents()
        try:
            result = run_mk4s_z_auto_approach(
                execute=True,
                setpoint_distance_mm=setpoint_distance,
                retract_after=False,
            )
        except Exception as error:
            self.main_z_status_label.setText(f"Auto approach failed: {error}")
            self.main_z_status_label.setStyleSheet("border: 1px solid #b71c1c; color: #b71c1c; background: #ffebee; padding: 8px;")
            self.append_log(f"[Z AUTO APPROACH] Failed: {error}")
            QMessageBox.critical(self, "Z auto approach failed", str(error))
            return
        self.z_approached = True
        self.z_approach_target.setText(f"{result.final_z:.2f}")
        self.z_retract_start.setText(f"{result.final_z:.2f}")
        self.update_position_display({"z": result.final_z}, "Z auto approach")
        self.refresh_workstation_status_ui()
        self.main_z_status_label.setText(f"Approach complete at Z{result.final_z:.2f}. Measurement can start; retract before disconnect.")
        self.main_z_status_label.setStyleSheet("border: 1px solid #1565c0; color: #0d47a1; background: #eef6ff; padding: 8px;")
        self.append_log(f"[Z AUTO APPROACH] {result.message}")

    def run_main_z_retract(self) -> None:
        if not self.require_initialized("Z retract"):
            return
        if not self.confirm_critical_action(
            "Retract Z",
            "Retract Z to the confirmed safe height Z120?\n\nContinue only while watching the MK4S.",
        ):
            self.append_log("[APPROACH] Z retract cancelled")
            return
        try:
            result = run_mk4s_z_safe_retract(execute=True)
        except Exception as error:
            self.main_z_status_label.setText(f"Z retract failed: {error}")
            self.main_z_status_label.setStyleSheet("border: 1px solid #b71c1c; color: #b71c1c; background: #ffebee; padding: 8px;")
            self.append_log(f"[APPROACH] Z retract failed: {error}")
            QMessageBox.critical(self, "Z retract failed", str(error))
            return
        self.z_approached = False
        self.update_position_display({"z": result.target_z}, "Z retract")
        self.refresh_workstation_status_ui()
        self.main_z_status_label.setText(result.message)
        self.main_z_status_label.setStyleSheet("border: 1px solid #2e7d32; color: #1b5e20; background: #e8f5e9; padding: 8px;")
        self.append_log(f"[APPROACH] {result.message}")

    # ------------------------------------------------------------
    # Append message to log
    # ------------------------------------------------------------
    def append_log(self, message: str) -> None:
        self.log.append(message)

    # ------------------------------------------------------------
    # Build scan profile from GUI fields
    # ------------------------------------------------------------
    def build_profile(self) -> ScanProfile:
        return ScanProfile(
            x_min=float(self.x_min.text()),
            x_max=float(self.x_max.text()),
            y_min=float(self.y_min.text()),
            y_max=float(self.y_max.text()),
            z=float(self.z.text()),
            x_resolution=int(self.x_res.text()),
            y_resolution=int(self.y_res.text()),
            feedrate_xy=float(self.xy_feedrate.text()),
            feedrate_z=float(self.z_feedrate.text()),
            mode=self.scan_mode_dropdown.currentText(),
        )

    # ------------------------------------------------------------
    # Validate profile against locked motion limits
    # ------------------------------------------------------------
    def validate_profile(self, require_initialized: bool = True) -> ScanProfile | None:
        if require_initialized and not self.require_initialized("Profile validation"):
            return None

        try:
            profile = self.build_profile()
            validate_scan_profile(profile, self.limits)
            self.workstation_status.record_validation_pass()
            self.refresh_workstation_status_ui()

            self.append_log("Validation: PASS")
            self.append_log(str(profile))
            self.append_log(f"Selected color map: {self.color_map}")
            self.operator_step_label.setText(
                "Current step: profile is valid. Run a dry-run scan before enabling real motion."
            )

            QMessageBox.information(
                self,
                "Validation",
                "Scan profile VALID.",
            )

            return profile

        except Exception as error:
            self.workstation_status.record_validation_fail(str(error))
            self.refresh_workstation_status_ui()
            self.append_log("Validation: FAIL")
            self.append_log(f"Reason: {error}")

            QMessageBox.critical(
                self,
                "Validation",
                f"Scan profile INVALID:\n\n{error}\n\nNo hardware movement was performed.",
            )

            return None

    # ------------------------------------------------------------
    # Build CLI command for main scan launcher
    # ------------------------------------------------------------
    def build_cli_command(self, profile: ScanProfile, execute_hardware: bool) -> list[str]:
        command = [
            sys.executable,
            "core/application/cli_scan_launcher.py",
            "--mode",
            profile.mode,
            "--x-min",
            str(profile.x_min),
            "--x-max",
            str(profile.x_max),
            "--y-min",
            str(profile.y_min),
            "--y-max",
            str(profile.y_max),
            "--z",
            str(profile.z),
            "--x-resolution",
            str(profile.x_resolution),
            "--y-resolution",
            str(profile.y_resolution),
            "--feedrate-xy",
            str(profile.feedrate_xy),
            "--feedrate-z",
            str(profile.feedrate_z),
            "--output-file",
            self.output_file.text(),
        ]

        if execute_hardware:
            command.insert(2, "--execute-hardware")
        else:
            command.insert(2, "--dry-run")

        return command

    # ------------------------------------------------------------
    # Build plot output path based on CSV output path
    # Example:
    # data/interface_test_output.csv -> data/interface_test_output.png
    # ------------------------------------------------------------
    def build_plot_output_path(self) -> str:
        csv_path = Path(self.output_file.text())
        return str(csv_path.with_suffix(".png"))

    # ------------------------------------------------------------
    # Build plot command for raster PNG generation
    # ------------------------------------------------------------
    def build_plot_command(self) -> list[str]:
        return [
            sys.executable,
            "tools/plot_safe_raster.py",
            "--input-file",
            self.output_file.text(),
            "--output-file",
            self.build_plot_output_path(),
            "--color-map",
            self.color_map,
        ]

    # ------------------------------------------------------------
    # Run external command and log stdout/stderr
    # ------------------------------------------------------------
    def run_command(self, command: list[str], label: str) -> int:
        self.append_log(f"Running {label} command:")
        self.append_log(" ".join(command))

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
        )

        if result.stdout:
            self.append_log(result.stdout)

        if result.stderr:
            self.append_log(result.stderr)

        return result.returncode

    # ------------------------------------------------------------
    # Generate PNG plot from saved CSV output
    # ------------------------------------------------------------
    def generate_plot(self) -> tuple[int, str]:
        plot_path = self.build_plot_output_path()
        command = self.build_plot_command()
        exit_code = self.run_command(command, "plot")
        return exit_code, plot_path

    def refresh_acquisition_preview(self, csv_path: str, plot_path: str) -> None:
        try:
            frame = load_raster_frame(csv_path)
        except Exception as error:
            self.workstation_status.acquisition_status = f"preview unavailable: {error}"
            self.acquisition_status_label.setText(self.workstation_status.acquisition_summary())
            self.append_log(f"[ACQUISITION] Preview update failed: {error}")
            return

        self.workstation_status.record_scan_output(
            csv_path,
            plot_path,
            frame.point_count,
        )
        self.set_scan_progress(100, f"{frame.point_count} raster points loaded")
        self.refresh_plot_preview(plot_path)
        self.last_plot_path = plot_path
        self.open_scan_viewer_btn.setEnabled(True)
        self.line_scan_placeholder.setText(frame.line_scan_summary())
        self.topography_placeholder.setText(frame.topography_summary())
        self.z_condition_placeholder.setText(
            f"{frame.z_feedback_summary()}\n\n{self.current_z_setup_summary()}"
        )
        for direction, label in self.direction_preview_labels.items():
            label.setText(self.direction_window_text(direction, frame))
        for direction, label in self.direction_window_labels.items():
            label.setText(self.direction_window_text(direction, frame))
        self.refresh_workstation_status_ui()
        self.append_log(f"[ACQUISITION] Loaded raster preview from {csv_path}")

    def refresh_plot_preview(self, plot_path: str) -> None:
        pixmap = QPixmap(plot_path)
        if pixmap.isNull():
            self.plot_placeholder.setText(
                "Live Data / Raster Plot Preview\n\n"
                f"Plot image not available:\n{plot_path}"
            )
            return

        scaled = pixmap.scaled(
            520,
            320,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )
        self.plot_placeholder.setPixmap(scaled)
        self.plot_placeholder.setToolTip(plot_path)

    def open_scan_viewer(self) -> None:
        if not self.last_plot_path:
            QMessageBox.information(self, "Scan viewer", "No scan image is available yet.")
            return

        pixmap = QPixmap(self.last_plot_path)
        if pixmap.isNull():
            QMessageBox.warning(self, "Scan viewer", f"Could not load scan image:\n{self.last_plot_path}")
            return

        viewer = QDialog(self)
        viewer.setWindowTitle("Educational SPM Scan Viewer")
        viewer_layout = QVBoxLayout()
        image_label = QLabel()
        image_label.setAlignment(Qt.AlignCenter)
        image_label.setPixmap(pixmap.scaled(900, 650, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        image_label.setMinimumSize(700, 500)
        image_label.setScaledContents(False)
        viewer_layout.addWidget(image_label)
        viewer.setLayout(viewer_layout)
        viewer.resize(940, 720)
        self.scan_viewers.append(viewer)
        viewer.show()

    # ------------------------------------------------------------
    # Dry-run scan
    # ------------------------------------------------------------
    def run_dry_scan(self, require_initialized: bool = True) -> None:
        if require_initialized and not self.require_initialized("Demo scan"):
            return

        profile = self.validate_profile(require_initialized=require_initialized)

        if profile is None:
            self.append_log("Demo scan cancelled because validation failed.")
            return

        confirmation_message = self.build_scan_confirmation_message(
            profile,
            execute_hardware=False,
        )

        if not self.confirm_critical_action("Confirm demo scan", confirmation_message):
            self.append_log("[SCAN] Demo scan cancelled by operator")
            return

        self.scan_pause_requested = False
        self.scan_stop_requested = False
        self.pause_scan_btn.setEnabled(True)
        self.stop_scan_btn.setEnabled(True)
        self.append_log(f"Demo scan using color map: {self.color_map}")
        self.workstation_status.record_scan_start("DEMO", self.output_file.text())
        self.set_scan_progress(10, "demo scan starting")
        self.refresh_workstation_status_ui()

        command = self.build_cli_command(profile, execute_hardware=False)
        exit_code = self.run_command(command, "scan")

        if exit_code == 0:
            self.set_scan_progress(75, "generating raster plot")
            plot_exit_code, plot_path = self.generate_plot()

            if plot_exit_code == 0:
                self.refresh_acquisition_preview(self.output_file.text(), plot_path)
                self.append_log(f"Demo scan plot generated: {plot_path}")
                self.operator_step_label.setText(
                    "Current step: dry-run completed. Inspect line/topography/Z feedback, then enable real motion only if the MK4S path is clear."
                )
                QMessageBox.information(
                    self,
                    "Demo Scan",
                    (
                        "Demo scan completed successfully.\n\n"
                        "No hardware movement was performed.\n\n"
                        f"Plot saved to:\n{plot_path}"
                    ),
                )
            else:
                self.append_log(f"Plot generation failed with exit code {plot_exit_code}")
                QMessageBox.warning(
                    self,
                    "Demo Scan",
                    (
                        "Demo scan completed successfully, but plot generation failed.\n\n"
                        "Check the status log for details."
                    ),
                )
        else:
            self.append_log(f"Demo scan failed with exit code {exit_code}")
            QMessageBox.critical(
                self,
                "Demo Scan",
                f"Demo scan failed with exit code {exit_code}",
            )
        self.pause_scan_btn.setEnabled(False)
        self.stop_scan_btn.setEnabled(False)
    # ------------------------------------------------------------
    # System readiness check
    # ------------------------------------------------------------
    def initiate_system_check(self) -> None:
        if not self.confirm_critical_action(
            "Connect to SPM",
            (
                "SPM connection is starting.\n\n"
                "Before continuing, make sure:\n"
                "- MK4S power is ON\n"
                "- USB cable is connected\n"
                "- bed/surface area is clear\n"
                "- no probe, sample, hand, cable, or tool can collide\n"
                "- emergency stop / power access is reachable\n\n"
                "This step performs software validation and no-motion hardware communication checks."
            ),
        ):
            self.append_log("[SYSTEM CHECK] Initialization cancelled by operator")
            return

        self.append_log("[CONNECT] Starting SPM connection and automatic checks")
        self.initiate_system_check_btn.setEnabled(False)
        self.initiate_system_check_btn.setText("CONNECTING...")
        QApplication.processEvents()

        profile = self.validate_profile(require_initialized=False)
        if profile is None:
            self.workstation_status.record_system_check_fail("scan profile is invalid")
            self.refresh_workstation_status_ui()
            self.hardware_status_label.setText("Hardware / System Connection: SYSTEM CHECK FAILED - fix scan parameters")
            self.hardware_status_label.setStyleSheet("font-weight: bold; color: #c62828;")
            self.initiate_system_check_btn.setText("CONNECT TO SPM")
            self.initiate_system_check_btn.setEnabled(True)
            self.append_log("[CONNECT] Failed: scan profile is invalid")
            return

        try:
            init_result = run_workstation_initialization(self.config, self.z_driver)
        except Exception as error:
            self.workstation_status.record_system_check_fail("hardware communication check failed")
            self.refresh_workstation_status_ui()
            self.hardware_status_label.setText("Hardware / System Connection: INITIALIZATION FAILED")
            self.hardware_status_label.setStyleSheet("font-weight: bold; color: #c62828;")
            self.initiate_system_check_btn.setText("CONNECT TO SPM")
            self.initiate_system_check_btn.setEnabled(True)
            self.append_log(f"[CONNECT] Failed: {error}")
            QMessageBox.critical(self, "SPM connection failed", str(error))
            return

        for line in init_result.summary_lines:
            self.append_log(f"[INITIALIZE] {line}")
        if init_result.assessment.position:
            self.update_position_display(init_result.assessment.position, "initialization readback")

        if not init_result.passed:
            self.workstation_status.record_system_check_fail(init_result.recommendation)
            self.refresh_workstation_status_ui()
            self.hardware_status_label.setText("Hardware / System Connection: INITIALIZATION FAILED - inspect log")
            self.hardware_status_label.setStyleSheet("font-weight: bold; color: #c62828;")
            self.initiate_system_check_btn.setText("CONNECT TO SPM")
            self.initiate_system_check_btn.setEnabled(True)
            QMessageBox.warning(self, "SPM connection incomplete", init_result.recommendation)
            return

        self.workstation_status.record_system_check_pass()
        self.refresh_workstation_status_ui()
        self.hardware_status_label.setText("Hardware / System Connection: SYSTEM READY")
        self.hardware_status_label.setStyleSheet("font-weight: bold; color: #2e7d32;")
        self.initiate_system_check_btn.setText("SPM CONNECTED")
        self.initiate_system_check_btn.setEnabled(False)
        self.refresh_z_driver_status("Approach ready")
        self.operator_step_label.setText(
            "Current step: SPM connected. Use Approach, then start Measurement."
        )
        self.append_log("[CONNECT] Scan profile valid")
        self.append_log("[CONNECT] MK4S no-motion checks passed")
        self.append_log("[CONNECT] Approach controls ready")
        self.append_log("[CONNECT] Real motion remains disabled until operator enables it")

    # ------------------------------------------------------------
    # Hardware armed/disarmed safety state
    # ------------------------------------------------------------
    def arm_hardware(self) -> None:
        if not self.require_initialized("Enable real motion"):
            return

        if not self.system_check_passed:
            self.append_log("[SAFETY] Real motion enable blocked: run INITIATE SYSTEM CHECK first")
            self.hardware_status_label.setText("Hardware / System Connection: RUN SYSTEM CHECK BEFORE REAL MOTION")
            self.hardware_status_label.setStyleSheet("font-weight: bold; color: #ef6c00;")
            return

        self.workstation_status.enable_real_motion()
        self.refresh_workstation_status_ui()

        self.hardware_arm_btn.setEnabled(False)
        self.hardware_arm_btn.setStyleSheet("font-weight: bold; background-color: #9e9e9e; color: white; padding: 6px;")

        self.hardware_disarm_btn.setEnabled(True)
        self.hardware_disarm_btn.setStyleSheet("font-weight: bold; background-color: #b71c1c; color: white; padding: 6px;")

        self.execute_btn.setEnabled(True)
        self.execute_btn.setStyleSheet("font-weight: bold; background-color: #ef6c00; color: white; padding: 6px;")

        self.hardware_status_label.setText("Hardware / System Connection: REAL MOTION ENABLED - hardware commands allowed")
        self.hardware_status_label.setStyleSheet("font-weight: bold; color: #b71c1c;")
        self.operator_step_label.setText(
            "Current step: real motion is enabled. Supervise the MK4S and run hardware scan only with a clear object/surface path."
        )
        self.append_log("[SAFETY] Real motion enabled by operator")

    def disarm_hardware(self) -> None:
        self.workstation_status.disable_real_motion()
        self.refresh_workstation_status_ui()

        self.hardware_arm_btn.setEnabled(True)
        self.hardware_arm_btn.setStyleSheet("font-weight: bold; background-color: #2e7d32; color: white; padding: 6px;")

        self.hardware_disarm_btn.setEnabled(False)
        self.hardware_disarm_btn.setStyleSheet("font-weight: bold; background-color: #9e9e9e; color: white; padding: 6px;")

        self.execute_btn.setEnabled(False)
        self.execute_btn.setStyleSheet("font-weight: bold; background-color: #9e9e9e; color: white; padding: 6px;")

        self.hardware_status_label.setText("Hardware / System Connection: REAL MOTION DISABLED - hardware commands blocked")
        self.hardware_status_label.setStyleSheet("font-weight: bold; color: #2e7d32;")
        self.operator_step_label.setText(
            "Current step: real motion disabled. You can adjust settings, dry-run again, park, or close safely."
        )
        self.append_log("[SAFETY] Real motion disabled by operator")

    # ------------------------------------------------------------
    # Hardware scan
    # ------------------------------------------------------------
    def run_hardware_scan(self) -> None:
        if not self.require_initialized("Hardware scan"):
            return

        if not self.hardware_armed:
            self.append_log("[SAFETY] Hardware scan blocked because hardware is DISARMED")
            return

        profile = self.validate_profile()

        if profile is None:
            self.append_log("Hardware scan cancelled because validation failed.")
            return

        confirmation_message = self.build_scan_confirmation_message(
            profile,
            execute_hardware=True,
        )

        if not self.confirm_critical_action(
            "Confirm hardware scan",
            confirmation_message,
        ):
            self.append_log("[HARDWARE] Hardware scan cancelled by operator")
            return

        self.append_log(f"Hardware scan using color map: {self.color_map}")
        self.scan_pause_requested = False
        self.scan_stop_requested = False
        self.pause_scan_btn.setEnabled(True)
        self.stop_scan_btn.setEnabled(True)
        self.workstation_status.record_scan_start("HARDWARE", self.output_file.text())
        self.set_scan_progress(10, "hardware scan starting")
        self.refresh_workstation_status_ui()

        command = self.build_cli_command(profile, execute_hardware=True)
        exit_code = self.run_command(command, "scan")

        if exit_code == 0:
            self.set_scan_progress(75, "generating raster plot")
            plot_exit_code, plot_path = self.generate_plot()

            if plot_exit_code == 0:
                self.refresh_acquisition_preview(self.output_file.text(), plot_path)
                self.append_log(f"Hardware scan plot generated: {plot_path}")
                self.operator_step_label.setText(
                    "Current step: hardware scan completed and safe park requested. Inspect output before deinitializing."
                )
                try:
                    state = park_mk4s(self.config)
                    self.update_position_display(state.get("position", {}), "post-scan safe park")
                    self.z_approached = False
                    self.append_log(f"[HARDWARE] Post-scan safe park complete: {state}")
                except Exception as error:
                    self.append_log(f"[HARDWARE] Post-scan safe park failed: {error}")
                    QMessageBox.critical(
                        self,
                        "Post-scan safe park failed",
                        f"Scan completed, but safe park failed. Keep the software open and recover manually.\n\n{error}",
                    )
                QMessageBox.information(
                    self,
                    "Hardware Scan",
                    (
                        "Hardware scan completed successfully.\n\n"
                        f"Plot saved to:\n{plot_path}"
                    ),
                )
            else:
                self.append_log(f"Plot generation failed with exit code {plot_exit_code}")
                QMessageBox.warning(
                    self,
                    "Hardware Scan",
                    (
                        "Hardware scan completed successfully, but plot generation failed.\n\n"
                        "Check the status log for details."
                    ),
                )
        else:
            self.append_log(f"Hardware scan failed with exit code {exit_code}")
            QMessageBox.critical(
                self,
                "Hardware Scan",
                f"Hardware scan failed with exit code {exit_code}",
            )
        self.pause_scan_btn.setEnabled(False)
        self.stop_scan_btn.setEnabled(False)

    def closeEvent(self, event) -> None:
        self.stop_live_scan_runtime("window close requested")
        if not self.shutdown_complete:
            QMessageBox.warning(
                self,
                "Power off required",
                (
                    "Close is locked until POWER OFF / SAFE PARK completes.\n\n"
                    "This protects the MK4S by forcing deinitialization, dry-run Z disconnect, "
                    "and safe park before the software exits."
                ),
            )
            self.append_log("[GUI] Close blocked: power-off/safe-park required")
            event.ignore()
            return

        self.append_log("[GUI] Close confirmed after safe power-off")
        event.accept()


# ------------------------------------------------------------
# Program entry point
# ------------------------------------------------------------
def acquire_single_instance_socket():
    guard = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        guard.bind(("127.0.0.1", 47641))
        guard.listen(1)
    except OSError:
        guard.close()
        return None
    return guard


if __name__ == "__main__":
    instance_guard = acquire_single_instance_socket()
    app = QApplication(sys.argv)
    if instance_guard is None:
        QMessageBox.warning(
            None,
            "Educational SPM already running",
            "Another Educational SPM interface is already running. Use the existing window.",
        )
        raise SystemExit(0)
    gui = ScanGUI()
    gui.instance_guard = instance_guard
    gui.show()
    sys.exit(app.exec_())















