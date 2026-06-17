# Phase 1 Z GUI Function Report

Goal: find where the GUI reads Z, creates ScanProfile, and starts scan movement.


## GUI function/class map with likely scan/Z relevance

- lines 74-770: `def __init__(self):`  score=5
- lines 771-784: `def create_direction_preview_label(self, direction: str) -> QLabel:`  score=1
- lines 785-791: `def build_tool_dialog(self, title: str, content_layout: QVBoxLayout, width: int, height: int) -> QDialog:`  score=1
- lines 807-811: `def open_z_regulation_window(self) -> None:`  score=2
- lines 812-814: `def open_z_tools_window(self) -> None:`  score=2
- lines 847-864: `def open_direction_window(self, direction: str) -> None:`  score=1
- lines 883-897: `def update_operation_mode(self, mode: str) -> None:`  score=1
- lines 919-946: `def documentation_markdown(self) -> str:`  score=1
- lines 948-966: `def fmt(axis: str) -> str:`  score=1
- lines 982-995: `def connect_scan_setting_updates(self) -> None:`  score=1
- lines 996-1040: `def apply_scan_mode_preset(self, mode: str, show_limits: bool = True) -> None:`  score=1
- lines 1041-1073: `def refresh_timing_estimate(self) -> None:`  score=1
- lines 1074-1082: `def current_z_setup_summary(self) -> str:`  score=2
- lines 1121-1137: `def z_axis_visual(self, current_z: float, start_z: float, target_z: float) -> str:`  score=2
- lines 1138-1146: `def show_z_training_visual(self, title: str, current_z: float, start_z: float, target_z: float) -> None:`  score=2
- lines 1147-1177: `def set_initialized_controls_enabled(self, enabled: bool) -> None:`  score=2
- lines 1194-1259: `def apply_instrument_style(self) -> None:`  score=1
- lines 1260-1292: `def refresh_workstation_status_ui(self) -> None:`  score=2
- lines 1351-1406: `def power_off_workstation(self) -> bool:`  score=2
- lines 1430-1458: `def start_live_demo_scan(self) -> None:`  score=3
- lines 1459-1473: `def build_live_scan_points(self, profile: ScanProfile) -> list[dict[str, float | str | int]]:`  score=1
- lines 1481-1491: `def synthetic_regulated_height(self, x: float, y: float, profile: ScanProfile) -> float:`  score=2
- lines 1492-1539: `def advance_live_scan(self) -> None:`  score=4
- lines 1540-1565: `def finish_live_scan(self, cancelled: bool) -> None:`  score=1
- lines 1566-1589: `def write_live_scan_csv(self, output_path: str) -> None:`  score=3
- lines 1594-1617: `def draw_live_line_scan(self) -> None:`  score=1
- lines 1618-1640: `def draw_live_topography(self) -> None:`  score=1
- lines 1662-1686: `def run_main_scan(self) -> None:`  score=2
- lines 1701-1720: `def set_z_connection_indicator(self, connected: bool) -> None:`  score=2
- lines 1731-1734: `def confirm_z_action(self, title: str, message: str) -> bool:`  score=2
- lines 1735-1762: `def build_scan_confirmation_message(`  score=3
- lines 1763-1783: `def refresh_z_driver_status(self, prefix: str = "Z dry-run status") -> None:`  score=2
- lines 1784-1799: `def report_z_failure(self, status_text: str, log_text: str) -> None:`  score=3
- lines 1800-1817: `def run_z_dry_connect(self) -> None:`  score=2
- lines 1818-1854: `def run_z_dry_move_test(self) -> None:`  score=2
- lines 1855-1936: `def run_z_dry_approach(self) -> None:`  score=2
- lines 1937-2018: `def run_z_dry_retract(self) -> None:`  score=2
- lines 2019-2036: `def run_z_dry_disconnect(self) -> None:`  score=2
- lines 2037-2047: `def run_main_z_create(self) -> None:`  score=2
- lines 2048-2056: `def run_main_z_move(self) -> None:`  score=2
- lines 2057-2089: `def run_main_z_manual_step(self, direction: str) -> None:`  score=2
- lines 2090-2135: `def run_main_z_auto_approach(self) -> None:`  score=2
- lines 2136-2162: `def run_main_z_retract(self) -> None:`  score=3
- lines 2169-2185: `def build_profile(self) -> ScanProfile:`  score=3
- lines 2186-2227: `def validate_profile(self, require_initialized: bool = True) -> ScanProfile | None:`  score=3
- lines 2228-2267: `def build_cli_command(self, profile: ScanProfile, execute_hardware: bool) -> list[str]:`  score=2
- lines 2318-2347: `def refresh_acquisition_preview(self, csv_path: str, plot_path: str) -> None:`  score=3
- lines 2348-2365: `def refresh_plot_preview(self, plot_path: str) -> None:`  score=1
- lines 2393-2464: `def run_dry_scan(self, require_initialized: bool = True) -> None:`  score=1
- lines 2465-2543: `def initiate_system_check(self) -> None:`  score=2
- lines 2596-2683: `def run_hardware_scan(self) -> None:`  score=2

## GUI exact contexts: Z-like controls

File: `core\application\gui_scan_launcher.py`


### Context around line 51

```python
   47:     MAX_SCAN_RESOLUTION,
   48: )
   49: from core.system.hardware_diagnostics import run_hardware_communication_report
   50: from core.system.hardware_profile import SPMHardwareProfile
>> 51: from core.system.mk4s_z_auto_approach import run_mk4s_z_auto_approach, run_mk4s_z_manual_step, run_mk4s_z_safe_retract
   52: from core.system.workstation_initializer import run_workstation_initialization
   53: from core.motion.prusa_gcode_backend import PrusaGcodeBackend
   54: from core.motion.parking import park_mk4s
   55: 
   56: from core.z_control.crtouch_probe_plan import CRTouchProbePlan
   57: from core.z_control.z_driver_arduino_safe import ZDriverArduino
   58: 
   59: 
```

### Context around line 56

```python
   52: from core.system.workstation_initializer import run_workstation_initialization
   53: from core.motion.prusa_gcode_backend import PrusaGcodeBackend
   54: from core.motion.parking import park_mk4s
   55: 
>> 56: from core.z_control.crtouch_probe_plan import CRTouchProbePlan
   57: from core.z_control.z_driver_arduino_safe import ZDriverArduino
   58: 
   59: 
   60: # ============================================================
   61: # SPM Educational GUI
   62: # Safe GUI wrapper around the verified CLI scan launcher
   63: # ============================================================
   64: APP_VERSION = "v0.25.0"
```

### Context around line 57

```python
   53: from core.motion.prusa_gcode_backend import PrusaGcodeBackend
   54: from core.motion.parking import park_mk4s
   55: 
   56: from core.z_control.crtouch_probe_plan import CRTouchProbePlan
>> 57: from core.z_control.z_driver_arduino_safe import ZDriverArduino
   58: 
   59: 
   60: # ============================================================
   61: # SPM Educational GUI
   62: # Safe GUI wrapper around the verified CLI scan launcher
   63: # ============================================================
   64: APP_VERSION = "v0.25.0"
   65: APP_PHASE = "Focused SPM Workflow - Connection, Approach, Measurement"
```

### Context around line 93

```python
   89:         self.scan_viewers = []
   90:         self.direction_viewers = {}
   91:         self.direction_preview_labels = {}
   92:         self.direction_window_labels = {}
>> 93:         self.z_approached = False
   94:         self.scan_stop_requested = False
   95:         self.scan_pause_requested = False
   96:         self.live_scan_timer = QTimer(self)
   97:         self.live_scan_timer.timeout.connect(self.advance_live_scan)
   98:         self.live_scan_points = []
   99:         self.live_scan_index = 0
   100:         self.live_scan_rows = []
   101:         self.live_scan_current_line = []
```

### Context around line 104

```python
   100:         self.live_scan_rows = []
   101:         self.live_scan_current_line = []
   102:         self.live_scan_profile = None
   103:         self.live_scan_active = False
>> 104:         self.live_scan_z_setpoint = float(self.config["scan_area"]["z"])
   105: 
   106:         # ------------------------------------------------------------
   107:         # Locked motion limits
   108:         # ------------------------------------------------------------
   109:         self.limits = MotionLimits(
   110:             x_min=self.config["motion_limits"]["x"][0],
   111:             x_max=self.config["motion_limits"]["x"][1],
   112:             y_min=self.config["motion_limits"]["y"][0],
```

### Context around line 114

```python
   110:             x_min=self.config["motion_limits"]["x"][0],
   111:             x_max=self.config["motion_limits"]["x"][1],
   112:             y_min=self.config["motion_limits"]["y"][0],
   113:             y_max=self.config["motion_limits"]["y"][1],
>> 114:             z_min=self.config["motion_limits"]["z"][0],
   115:             z_max=self.config["motion_limits"]["z"][1],
   116:         )
   117: 
   118:         scan_area = self.config["scan_area"]
   119: 
   120:         # ------------------------------------------------------------
   121:         # Layouts
   122:         # ------------------------------------------------------------
```

### Context around line 115

```python
   111:             x_max=self.config["motion_limits"]["x"][1],
   112:             y_min=self.config["motion_limits"]["y"][0],
   113:             y_max=self.config["motion_limits"]["y"][1],
   114:             z_min=self.config["motion_limits"]["z"][0],
>> 115:             z_max=self.config["motion_limits"]["z"][1],
   116:         )
   117: 
   118:         scan_area = self.config["scan_area"]
   119: 
   120:         # ------------------------------------------------------------
   121:         # Layouts
   122:         # ------------------------------------------------------------
   123:         main_layout = QVBoxLayout()
```

### Context around line 137

```python
   133:         self.z = QLineEdit(str(scan_area["z"]))
   134:         self.x_res = QLineEdit(str(scan_area["x_resolution"]))
   135:         self.y_res = QLineEdit(str(scan_area["y_resolution"]))
   136:         self.xy_feedrate = QLineEdit(str(self.safe_feedrates["xy"]))
>> 137:         self.z_feedrate = QLineEdit(str(self.safe_feedrates["z"]))
   138:         self.z_dwell_ms = QLineEdit("50")
   139:         self.line_time_estimate_label = QLabel("Line time: waiting for scan settings")
   140:         self.frame_time_estimate_label = QLabel("Frame time: waiting for scan settings")
   141:         self.mode_readiness_label = QLabel("")
   142:         self.mode_readiness_label.setWordWrap(True)
   143: 
   144:         # ------------------------------------------------------------
   145:         # Output CSV path
```

### Context around line 138

```python
   134:         self.x_res = QLineEdit(str(scan_area["x_resolution"]))
   135:         self.y_res = QLineEdit(str(scan_area["y_resolution"]))
   136:         self.xy_feedrate = QLineEdit(str(self.safe_feedrates["xy"]))
   137:         self.z_feedrate = QLineEdit(str(self.safe_feedrates["z"]))
>> 138:         self.z_dwell_ms = QLineEdit("50")
   139:         self.line_time_estimate_label = QLabel("Line time: waiting for scan settings")
   140:         self.frame_time_estimate_label = QLabel("Frame time: waiting for scan settings")
   141:         self.mode_readiness_label = QLabel("")
   142:         self.mode_readiness_label.setWordWrap(True)
   143: 
   144:         # ------------------------------------------------------------
   145:         # Output CSV path
   146:         # ------------------------------------------------------------
```

### Context around line 195

```python
   191:         self.open_scan_setup_btn = QPushButton("MEASUREMENT SETUP")
   192:         self.open_scan_setup_btn.clicked.connect(self.open_measurement_window)
   193:         self.open_xy_scanner_btn = QPushButton("XY SCANNER")
   194:         self.open_xy_scanner_btn.clicked.connect(self.open_xy_scanner_window)
>> 195:         self.open_z_regulation_btn = QPushButton("SERVICE APPROACH")
   196:         self.open_z_regulation_btn.clicked.connect(self.open_z_regulation_window)
   197:         self.open_hardware_tools_btn = QPushButton("HARDWARE CHECK")
   198:         self.open_hardware_tools_btn.clicked.connect(self.open_hardware_tools_window)
   199:         self.hardware_check_btn = QPushButton("RUN HARDWARE CHECK")
   200:         self.hardware_check_btn.clicked.connect(self.run_hardware_check_only)
   201:         self.open_z_tools_btn = QPushButton("Z / APPROACH")
   202:         self.open_z_tools_btn.clicked.connect(self.open_measurement_window)
   203:         self.about_btn = QPushButton("ABOUT")
```

### Context around line 196

```python
   192:         self.open_scan_setup_btn.clicked.connect(self.open_measurement_window)
   193:         self.open_xy_scanner_btn = QPushButton("XY SCANNER")
   194:         self.open_xy_scanner_btn.clicked.connect(self.open_xy_scanner_window)
   195:         self.open_z_regulation_btn = QPushButton("SERVICE APPROACH")
>> 196:         self.open_z_regulation_btn.clicked.connect(self.open_z_regulation_window)
   197:         self.open_hardware_tools_btn = QPushButton("HARDWARE CHECK")
   198:         self.open_hardware_tools_btn.clicked.connect(self.open_hardware_tools_window)
   199:         self.hardware_check_btn = QPushButton("RUN HARDWARE CHECK")
   200:         self.hardware_check_btn.clicked.connect(self.run_hardware_check_only)
   201:         self.open_z_tools_btn = QPushButton("Z / APPROACH")
   202:         self.open_z_tools_btn.clicked.connect(self.open_measurement_window)
   203:         self.about_btn = QPushButton("ABOUT")
   204:         self.about_btn.clicked.connect(self.show_about)
```

### Context around line 201

```python
   197:         self.open_hardware_tools_btn = QPushButton("HARDWARE CHECK")
   198:         self.open_hardware_tools_btn.clicked.connect(self.open_hardware_tools_window)
   199:         self.hardware_check_btn = QPushButton("RUN HARDWARE CHECK")
   200:         self.hardware_check_btn.clicked.connect(self.run_hardware_check_only)
>> 201:         self.open_z_tools_btn = QPushButton("Z / APPROACH")
   202:         self.open_z_tools_btn.clicked.connect(self.open_measurement_window)
   203:         self.about_btn = QPushButton("ABOUT")
   204:         self.about_btn.clicked.connect(self.show_about)
   205: 
   206:         self.direction_buttons = {}
   207:         for direction, label in (
   208:             ("forward", "X+ TOPOGRAPHY"),
   209:             ("backward", "X- TOPOGRAPHY"),
```

### Context around line 202

```python
   198:         self.open_hardware_tools_btn.clicked.connect(self.open_hardware_tools_window)
   199:         self.hardware_check_btn = QPushButton("RUN HARDWARE CHECK")
   200:         self.hardware_check_btn.clicked.connect(self.run_hardware_check_only)
   201:         self.open_z_tools_btn = QPushButton("Z / APPROACH")
>> 202:         self.open_z_tools_btn.clicked.connect(self.open_measurement_window)
   203:         self.about_btn = QPushButton("ABOUT")
   204:         self.about_btn.clicked.connect(self.show_about)
   205: 
   206:         self.direction_buttons = {}
   207:         for direction, label in (
   208:             ("forward", "X+ TOPOGRAPHY"),
   209:             ("backward", "X- TOPOGRAPHY"),
   210:             ("upward", "Y+ TOPOGRAPHY"),
```

### Context around line 243

```python
   239:         # Safe Z-control dry-run driver
   240:         # These controls do not move real hardware.
   241:         # They only test the Phase 5.1 Arduino/Z-control software path.
   242:         # ------------------------------------------------------------
>> 243:         self.z_driver = ZDriverArduino(dry_run=True)
   244: 
   245:         self.z_status_label = QLabel("Z dry-run status: Disconnected")
   246:         self.z_connection_state_label = QLabel("? READY TO CONNECT")
   247:         self.z_connection_state_label.setStyleSheet("font-weight: bold; color: #c62828;")
   248:         self.z_test_position = QLineEdit("20")
   249: 
   250:         self.z_approach_start = QLineEdit("20")
   251:         self.z_approach_target = QLineEdit("17")
```

### Context around line 245

```python
   241:         # They only test the Phase 5.1 Arduino/Z-control software path.
   242:         # ------------------------------------------------------------
   243:         self.z_driver = ZDriverArduino(dry_run=True)
   244: 
>> 245:         self.z_status_label = QLabel("Z dry-run status: Disconnected")
   246:         self.z_connection_state_label = QLabel("? READY TO CONNECT")
   247:         self.z_connection_state_label.setStyleSheet("font-weight: bold; color: #c62828;")
   248:         self.z_test_position = QLineEdit("20")
   249: 
   250:         self.z_approach_start = QLineEdit("20")
   251:         self.z_approach_target = QLineEdit("17")
   252:         self.z_retract_start = QLineEdit("17")
   253:         self.z_retract_target = QLineEdit("20")
```

### Context around line 246

```python
   242:         # ------------------------------------------------------------
   243:         self.z_driver = ZDriverArduino(dry_run=True)
   244: 
   245:         self.z_status_label = QLabel("Z dry-run status: Disconnected")
>> 246:         self.z_connection_state_label = QLabel("? READY TO CONNECT")
   247:         self.z_connection_state_label.setStyleSheet("font-weight: bold; color: #c62828;")
   248:         self.z_test_position = QLineEdit("20")
   249: 
   250:         self.z_approach_start = QLineEdit("20")
   251:         self.z_approach_target = QLineEdit("17")
   252:         self.z_retract_start = QLineEdit("17")
   253:         self.z_retract_target = QLineEdit("20")
   254:         self.z_step_size = QLineEdit("1")
```

### Context around line 247

```python
   243:         self.z_driver = ZDriverArduino(dry_run=True)
   244: 
   245:         self.z_status_label = QLabel("Z dry-run status: Disconnected")
   246:         self.z_connection_state_label = QLabel("? READY TO CONNECT")
>> 247:         self.z_connection_state_label.setStyleSheet("font-weight: bold; color: #c62828;")
   248:         self.z_test_position = QLineEdit("20")
   249: 
   250:         self.z_approach_start = QLineEdit("20")
   251:         self.z_approach_target = QLineEdit("17")
   252:         self.z_retract_start = QLineEdit("17")
   253:         self.z_retract_target = QLineEdit("20")
   254:         self.z_step_size = QLineEdit("1")
   255: 
```

### Context around line 248

```python
   244: 
   245:         self.z_status_label = QLabel("Z dry-run status: Disconnected")
   246:         self.z_connection_state_label = QLabel("? READY TO CONNECT")
   247:         self.z_connection_state_label.setStyleSheet("font-weight: bold; color: #c62828;")
>> 248:         self.z_test_position = QLineEdit("20")
   249: 
   250:         self.z_approach_start = QLineEdit("20")
   251:         self.z_approach_target = QLineEdit("17")
   252:         self.z_retract_start = QLineEdit("17")
   253:         self.z_retract_target = QLineEdit("20")
   254:         self.z_step_size = QLineEdit("1")
   255: 
   256:         self.z_connect_btn = QPushButton("Z Dry Run: Connect")
```

## GUI exact contexts: ScanProfile creation / scan start / preview

File: `core\application\gui_scan_launcher.py`


### Context around line 42

```python
   38: 
   39: from core.acquisition.raster_stream import load_raster_frame
   40: from core.application.workstation_status import WorkstationStatus
   41: from core.education.config_loader import load_config, get_safe_feedrates, get_scan_mode_preset
>> 42: from core.education.scan_profile import (
   43:     ScanProfile,
   44:     MotionLimits,
   45:     VALID_SCAN_MODES,
   46:     validate_scan_profile,
   47:     MAX_SCAN_RESOLUTION,
   48: )
   49: from core.system.hardware_diagnostics import run_hardware_communication_report
   50: from core.system.hardware_profile import SPMHardwareProfile
```

### Context around line 46

```python
   42: from core.education.scan_profile import (
   43:     ScanProfile,
   44:     MotionLimits,
   45:     VALID_SCAN_MODES,
>> 46:     validate_scan_profile,
   47:     MAX_SCAN_RESOLUTION,
   48: )
   49: from core.system.hardware_diagnostics import run_hardware_communication_report
   50: from core.system.hardware_profile import SPMHardwareProfile
   51: from core.system.mk4s_z_auto_approach import run_mk4s_z_auto_approach, run_mk4s_z_manual_step, run_mk4s_z_safe_retract
   52: from core.system.workstation_initializer import run_workstation_initialization
   53: from core.motion.prusa_gcode_backend import PrusaGcodeBackend
   54: from core.motion.parking import park_mk4s
```

### Context around line 91

```python
   87:         self.shutdown_complete = False
   88:         self.last_plot_path = ""
   89:         self.scan_viewers = []
   90:         self.direction_viewers = {}
>> 91:         self.direction_preview_labels = {}
   92:         self.direction_window_labels = {}
   93:         self.z_approached = False
   94:         self.scan_stop_requested = False
   95:         self.scan_pause_requested = False
   96:         self.live_scan_timer = QTimer(self)
   97:         self.live_scan_timer.timeout.connect(self.advance_live_scan)
   98:         self.live_scan_points = []
   99:         self.live_scan_index = 0
```

### Context around line 102

```python
   98:         self.live_scan_points = []
   99:         self.live_scan_index = 0
   100:         self.live_scan_rows = []
   101:         self.live_scan_current_line = []
>> 102:         self.live_scan_profile = None
   103:         self.live_scan_active = False
   104:         self.live_scan_z_setpoint = float(self.config["scan_area"]["z"])
   105: 
   106:         # ------------------------------------------------------------
   107:         # Locked motion limits
   108:         # ------------------------------------------------------------
   109:         self.limits = MotionLimits(
   110:             x_min=self.config["motion_limits"]["x"][0],
```

### Context around line 133

```python
   129:         self.x_min = QLineEdit(str(scan_area["x_min"]))
   130:         self.x_max = QLineEdit(str(scan_area["x_max"]))
   131:         self.y_min = QLineEdit(str(scan_area["y_min"]))
   132:         self.y_max = QLineEdit(str(scan_area["y_max"]))
>> 133:         self.z = QLineEdit(str(scan_area["z"]))
   134:         self.x_res = QLineEdit(str(scan_area["x_resolution"]))
   135:         self.y_res = QLineEdit(str(scan_area["y_resolution"]))
   136:         self.xy_feedrate = QLineEdit(str(self.safe_feedrates["xy"]))
   137:         self.z_feedrate = QLineEdit(str(self.safe_feedrates["z"]))
   138:         self.z_dwell_ms = QLineEdit("50")
   139:         self.line_time_estimate_label = QLabel("Line time: waiting for scan settings")
   140:         self.frame_time_estimate_label = QLabel("Frame time: waiting for scan settings")
   141:         self.mode_readiness_label = QLabel("")
```

### Context around line 359

```python
   355:         self.main_z_up_btn = QPushButton("MANUAL UP")
   356:         self.main_z_up_btn.clicked.connect(lambda: self.run_main_z_manual_step("up"))
   357:         self.main_z_down_btn = QPushButton("MANUAL DOWN")
   358:         self.main_z_down_btn.clicked.connect(lambda: self.run_main_z_manual_step("down"))
>> 359:         self.plot_placeholder = QLabel("Live Data / Raster Plot Preview\n\nPlaceholder for last generated PNG, future live raster image, and signal monitor.")
   360:         self.plot_placeholder.setStyleSheet("border: 1px solid #9e9e9e; padding: 12px; background-color: #fafafa;")
   361:         self.plot_placeholder.setFixedSize(460, 260)
   362:         self.plot_placeholder.setAlignment(Qt.AlignCenter)
   363:         self.plot_placeholder.setScaledContents(False)
   364:         self.plot_placeholder.setWordWrap(True)
   365: 
   366:         self.line_scan_placeholder = QLabel(
   367:             f"1D Line Scan\n\nWaiting for scan data.\nFrame capacity: {MAX_SCAN_RESOLUTION} samples per line."
```

### Context around line 375

```python
   371:         self.line_scan_placeholder.setFixedSize(460, 145)
   372:         self.line_scan_placeholder.setWordWrap(True)
   373: 
   374:         self.topography_placeholder = QLabel(
>> 375:             f"2D Topography Scan\n\nWaiting for raster/topography data.\nPreview frame is fixed; max input resolution is {MAX_SCAN_RESOLUTION} x {MAX_SCAN_RESOLUTION}."
   376:         )
   377:         self.topography_placeholder.setTextInteractionFlags(Qt.TextSelectableByMouse)
   378:         self.topography_placeholder.setStyleSheet("border: 1px solid #90a4ae; padding: 10px; background-color: #ffffff;")
   379:         self.topography_placeholder.setFixedSize(460, 220)
   380:         self.topography_placeholder.setWordWrap(True)
   381: 
   382:         self.z_condition_placeholder = QLabel("Z Condition / Feedback\n\nZ position: waiting\nApproach state: waiting\nSignal / height feedback: waiting")
   383:         self.z_condition_placeholder.setTextInteractionFlags(Qt.TextSelectableByMouse)
```

### Context around line 510

```python
   506:         z_connection_layout.addLayout(z_connection_bar)
   507:         z_connection_layout.addWidget(self.z_status_label)
   508:         z_connection_group.setLayout(z_connection_layout)
   509: 
>> 510:         z_move_group = QGroupBox("Manual Z Move Preview")
   511:         z_move_layout = QVBoxLayout()
   512:         z_move_layout.addWidget(self.z_move_test_btn)
   513:         z_move_group.setLayout(z_move_layout)
   514: 
   515:         z_approach_group = QGroupBox("Auto Approach Preview")
   516:         z_approach_layout = QFormLayout()
   517:         z_approach_layout.addRow("Approach start Z:", self.z_approach_start)
   518:         z_approach_layout.addRow("Approach target Z:", self.z_approach_target)
```

### Context around line 515

```python
   511:         z_move_layout = QVBoxLayout()
   512:         z_move_layout.addWidget(self.z_move_test_btn)
   513:         z_move_group.setLayout(z_move_layout)
   514: 
>> 515:         z_approach_group = QGroupBox("Auto Approach Preview")
   516:         z_approach_layout = QFormLayout()
   517:         z_approach_layout.addRow("Approach start Z:", self.z_approach_start)
   518:         z_approach_layout.addRow("Approach target Z:", self.z_approach_target)
   519:         z_approach_layout.addRow("Z step size:", self.z_step_size)
   520:         z_approach_layout.addRow("", self.z_approach_btn)
   521:         z_approach_group.setLayout(z_approach_layout)
   522: 
   523:         z_retract_group = QGroupBox("Safe Retract Preview")
```

### Context around line 523

```python
   519:         z_approach_layout.addRow("Z step size:", self.z_step_size)
   520:         z_approach_layout.addRow("", self.z_approach_btn)
   521:         z_approach_group.setLayout(z_approach_layout)
   522: 
>> 523:         z_retract_group = QGroupBox("Safe Retract Preview")
   524:         z_retract_layout = QFormLayout()
   525:         z_retract_layout.addRow("Retract start Z:", self.z_retract_start)
   526:         z_retract_layout.addRow("Retract target Z:", self.z_retract_target)
   527:         z_retract_layout.addRow("", self.z_retract_btn)
   528:         z_retract_group.setLayout(z_retract_layout)
   529: 
   530:         z_layout.addWidget(z_height_group)
   531:         z_layout.addWidget(z_connection_group)
```

### Context around line 572

```python
   568:         right_panel.addWidget(z_group)
   569:         right_panel.addStretch()
   570: 
   571:         # Legacy tab strings retained for source-history tests:
>> 572:         # feedback_tabs.addTab(self.plot_placeholder, "Raster Preview")
   573:         # feedback_tabs.addTab(self.line_scan_placeholder, "Line Scan")
   574:         # feedback_tabs.addTab(self.topography_placeholder, "Topography")
   575: 
   576:         z_feedback_tab = QWidget()
   577:         z_feedback_layout = QVBoxLayout()
   578:         z_feedback_layout.addWidget(self.z_condition_placeholder)
   579:         z_feedback_layout.addWidget(self.z_probe_plan_label)
   580:         z_feedback_layout.addWidget(self.z_probe_safety_label)
```

### Context around line 771

```python
   767: 
   768:     # ------------------------------------------------------------
   769:     # Select output CSV file
   770:     # ------------------------------------------------------------
>> 771:     def create_direction_preview_label(self, direction: str) -> QLabel:
   772:         title = direction.upper()
   773:         label = QLabel(
   774:             f"{title} IMAGE\n\n"
   775:             "Waiting for scan data.\n"
   776:             "This fixed frame will show topography and line information for this raster direction."
   777:         )
   778:         label.setTextInteractionFlags(Qt.TextSelectableByMouse)
   779:         label.setStyleSheet("border: 1px solid #90a4ae; padding: 10px; background-color: #ffffff;")
```

### Context around line 852

```python
   848:         if direction not in self.direction_viewers:
   849:             dialog = QDialog(self)
   850:             dialog.setWindowTitle(f"Educational SPM {APP_VERSION} - {direction.title()} Image")
   851:             layout = QVBoxLayout()
>> 852:             label = self.create_direction_preview_label(direction)
   853:             label.setFixedSize(430, 260)
   854:             layout.addWidget(label)
   855:             dialog.setLayout(layout)
   856:             dialog.resize(470, 320)
   857:             self.direction_viewers[direction] = dialog
   858:             self.direction_window_labels[direction] = label
   859: 
   860:         viewer = self.direction_viewers[direction]
```

### Context around line 1438

```python
   1434:             return
   1435: 
   1436:         self.scan_pause_requested = False
   1437:         self.scan_stop_requested = False
>> 1438:         self.live_scan_profile = profile
   1439:         self.live_scan_z_setpoint = profile.z
   1440:         self.live_scan_rows = []
   1441:         self.live_scan_current_line = []
   1442:         self.live_scan_points = self.build_live_scan_points(profile)
   1443:         self.live_scan_index = 0
   1444:         self.live_scan_active = True
   1445:         self.pause_scan_btn.setEnabled(True)
   1446:         self.stop_scan_btn.setEnabled(True)
```

### Context around line 1439

```python
   1435: 
   1436:         self.scan_pause_requested = False
   1437:         self.scan_stop_requested = False
   1438:         self.live_scan_profile = profile
>> 1439:         self.live_scan_z_setpoint = profile.z
   1440:         self.live_scan_rows = []
   1441:         self.live_scan_current_line = []
   1442:         self.live_scan_points = self.build_live_scan_points(profile)
   1443:         self.live_scan_index = 0
   1444:         self.live_scan_active = True
   1445:         self.pause_scan_btn.setEnabled(True)
   1446:         self.stop_scan_btn.setEnabled(True)
   1447:         self.main_scan_btn.setEnabled(False)
```

### Context around line 1490

```python
   1486:         terrace = 0.55 if nx > 0.58 and ny > 0.32 else 0.0
   1487:         lattice = 0.18 * math.sin(nx * math.pi * 18.0) * math.cos(ny * math.pi * 14.0)
   1488:         slope = 0.28 * nx + 0.16 * ny
   1489:         ridge = 0.45 * math.exp(-((nx - 0.72) ** 2 + (ny - 0.68) ** 2) / 0.012)
>> 1490:         return profile.z + slope + terrace + lattice + ridge
   1491: 
   1492:     def advance_live_scan(self) -> None:
   1493:         if self.scan_stop_requested:
   1494:             self.finish_live_scan(cancelled=True)
   1495:             return
   1496: 
   1497:         if self.scan_pause_requested:
   1498:             self.live_scan_status_label.setText("Live scan: paused. Press SCAN DEMO again to restart or STOP to cancel.")
```

### Context around line 1501

```python
   1497:         if self.scan_pause_requested:
   1498:             self.live_scan_status_label.setText("Live scan: paused. Press SCAN DEMO again to restart or STOP to cancel.")
   1499:             return
   1500: 
>> 1501:         if not self.live_scan_profile:
   1502:             self.finish_live_scan(cancelled=True)
   1503:             return
   1504: 
   1505:         points_per_tick = 4
   1506:         for _ in range(points_per_tick):
   1507:             if self.live_scan_index >= len(self.live_scan_points):
   1508:                 self.finish_live_scan(cancelled=False)
   1509:                 return
```

### Context around line 1511

```python
   1507:             if self.live_scan_index >= len(self.live_scan_points):
   1508:                 self.finish_live_scan(cancelled=False)
   1509:                 return
   1510:             point = self.live_scan_points[self.live_scan_index]
>> 1511:             z_value = self.synthetic_regulated_height(float(point["x"]), float(point["y"]), self.live_scan_profile)
   1512:             sample = {
   1513:                 "timestamp": datetime.now().isoformat(timespec="seconds"),
   1514:                 "scan_direction": str(point["x_direction"]),
   1515:                 "y_pass": str(point["y_pass"]),
   1516:                 "line": int(point["line"]),
   1517:                 "target_x": float(point["x"]),
   1518:                 "target_y": float(point["y"]),
   1519:                 "actual_x": float(point["x"]),
```

## CLI ScanProfile creation

File: `core\application\cli_scan_launcher.py`


### Context around line 26

```python
   22: def build_scan_profile_from_config(config: dict, mode: str) -> ScanProfile:
   23:     scan_area = config["scan_area"]
   24:     safe_feedrates = get_safe_feedrates(config)
   25: 
>> 26:     return ScanProfile(
   27:         x_min=scan_area["x_min"],
   28:         x_max=scan_area["x_max"],
   29:         y_min=scan_area["y_min"],
   30:         y_max=scan_area["y_max"],
   31:         z=scan_area["z"],
   32:         x_resolution=scan_area["x_resolution"],
   33:         y_resolution=scan_area["y_resolution"],
   34:         feedrate_xy=safe_feedrates["xy"],
```

### Context around line 31

```python
   27:         x_min=scan_area["x_min"],
   28:         x_max=scan_area["x_max"],
   29:         y_min=scan_area["y_min"],
   30:         y_max=scan_area["y_max"],
>> 31:         z=scan_area["z"],
   32:         x_resolution=scan_area["x_resolution"],
   33:         y_resolution=scan_area["y_resolution"],
   34:         feedrate_xy=safe_feedrates["xy"],
   35:         feedrate_z=safe_feedrates["z"],
   36:         mode=mode,
   37:     )
   38: 
   39: 
```

### Context around line 35

```python
   31:         z=scan_area["z"],
   32:         x_resolution=scan_area["x_resolution"],
   33:         y_resolution=scan_area["y_resolution"],
   34:         feedrate_xy=safe_feedrates["xy"],
>> 35:         feedrate_z=safe_feedrates["z"],
   36:         mode=mode,
   37:     )
   38: 
   39: 
   40: def apply_cli_overrides(profile: ScanProfile, args: argparse.Namespace) -> ScanProfile:
   41:     return ScanProfile(
   42:         x_min=args.x_min if args.x_min is not None else profile.x_min,
   43:         x_max=args.x_max if args.x_max is not None else profile.x_max,
```

### Context around line 41

```python
   37:     )
   38: 
   39: 
   40: def apply_cli_overrides(profile: ScanProfile, args: argparse.Namespace) -> ScanProfile:
>> 41:     return ScanProfile(
   42:         x_min=args.x_min if args.x_min is not None else profile.x_min,
   43:         x_max=args.x_max if args.x_max is not None else profile.x_max,
   44:         y_min=args.y_min if args.y_min is not None else profile.y_min,
   45:         y_max=args.y_max if args.y_max is not None else profile.y_max,
   46:         z=args.z if args.z is not None else profile.z,
   47:         x_resolution=args.x_resolution if args.x_resolution is not None else profile.x_resolution,
   48:         y_resolution=args.y_resolution if args.y_resolution is not None else profile.y_resolution,
   49:         feedrate_xy=args.feedrate_xy if getattr(args, "feedrate_xy", None) is not None else profile.feedrate_xy,
```

### Context around line 46

```python
   42:         x_min=args.x_min if args.x_min is not None else profile.x_min,
   43:         x_max=args.x_max if args.x_max is not None else profile.x_max,
   44:         y_min=args.y_min if args.y_min is not None else profile.y_min,
   45:         y_max=args.y_max if args.y_max is not None else profile.y_max,
>> 46:         z=args.z if args.z is not None else profile.z,
   47:         x_resolution=args.x_resolution if args.x_resolution is not None else profile.x_resolution,
   48:         y_resolution=args.y_resolution if args.y_resolution is not None else profile.y_resolution,
   49:         feedrate_xy=args.feedrate_xy if getattr(args, "feedrate_xy", None) is not None else profile.feedrate_xy,
   50:         feedrate_z=args.feedrate_z if getattr(args, "feedrate_z", None) is not None else profile.feedrate_z,
   51:         mode=profile.mode,
   52:     )
   53: 
   54: 
```

### Context around line 50

```python
   46:         z=args.z if args.z is not None else profile.z,
   47:         x_resolution=args.x_resolution if args.x_resolution is not None else profile.x_resolution,
   48:         y_resolution=args.y_resolution if args.y_resolution is not None else profile.y_resolution,
   49:         feedrate_xy=args.feedrate_xy if getattr(args, "feedrate_xy", None) is not None else profile.feedrate_xy,
>> 50:         feedrate_z=args.feedrate_z if getattr(args, "feedrate_z", None) is not None else profile.feedrate_z,
   51:         mode=profile.mode,
   52:     )
   53: 
   54: 
   55: def build_motion_limits_from_config(config: dict) -> MotionLimits:
   56:     motion_limits = config["motion_limits"]
   57: 
   58:     return MotionLimits(
```

### Context around line 63

```python
   59:         x_min=motion_limits["x"][0],
   60:         x_max=motion_limits["x"][1],
   61:         y_min=motion_limits["y"][0],
   62:         y_max=motion_limits["y"][1],
>> 63:         z_min=motion_limits["z"][0],
   64:         z_max=motion_limits["z"][1],
   65:     )
   66: 
   67: 
   68: def build_hardware_command(
   69:     profile: ScanProfile,
   70:     output_file: str | None = None,
   71:     dry_run: bool = False,
```

### Context around line 64

```python
   60:         x_max=motion_limits["x"][1],
   61:         y_min=motion_limits["y"][0],
   62:         y_max=motion_limits["y"][1],
   63:         z_min=motion_limits["z"][0],
>> 64:         z_max=motion_limits["z"][1],
   65:     )
   66: 
   67: 
   68: def build_hardware_command(
   69:     profile: ScanProfile,
   70:     output_file: str | None = None,
   71:     dry_run: bool = False,
   72: ) -> list[str]:
```

## ScanProfile validation

File: `core\education\scan_profile.py`


### Context around line 10

```python
   6:     x_min: float
   7:     x_max: float
   8:     y_min: float
   9:     y_max: float
>> 10:     z_min: float
   11:     z_max: float
   12: 
   13: 
   14: @dataclass(frozen=True)
   15: class ScanProfile:
   16:     x_min: float
   17:     x_max: float
   18:     y_min: float
```

### Context around line 11

```python
   7:     x_max: float
   8:     y_min: float
   9:     y_max: float
   10:     z_min: float
>> 11:     z_max: float
   12: 
   13: 
   14: @dataclass(frozen=True)
   15: class ScanProfile:
   16:     x_min: float
   17:     x_max: float
   18:     y_min: float
   19:     y_max: float
```

### Context around line 15

```python
   11:     z_max: float
   12: 
   13: 
   14: @dataclass(frozen=True)
>> 15: class ScanProfile:
   16:     x_min: float
   17:     x_max: float
   18:     y_min: float
   19:     y_max: float
   20:     z: float
   21:     x_resolution: int
   22:     y_resolution: int
   23:     feedrate_xy: float
```

### Context around line 20

```python
   16:     x_min: float
   17:     x_max: float
   18:     y_min: float
   19:     y_max: float
>> 20:     z: float
   21:     x_resolution: int
   22:     y_resolution: int
   23:     feedrate_xy: float
   24:     feedrate_z: float
   25:     mode: str = "SIMULATED_SURFACE"
   26: 
   27: 
   28: VALID_SCAN_MODES = {
```

### Context around line 24

```python
   20:     z: float
   21:     x_resolution: int
   22:     y_resolution: int
   23:     feedrate_xy: float
>> 24:     feedrate_z: float
   25:     mode: str = "SIMULATED_SURFACE"
   26: 
   27: 
   28: VALID_SCAN_MODES = {
   29:     "SIMULATED_SURFACE",
   30:     "CONTACT_PROBE",
   31:     "AFM_CONTACT",
   32:     "STM_DEMO",
```

### Context around line 39

```python
   35: 
   36: MAX_SCAN_RESOLUTION = 250
   37: 
   38: 
>> 39: def validate_scan_profile(profile: ScanProfile, limits: MotionLimits) -> None:
   40:     if profile.mode not in VALID_SCAN_MODES:
   41:         raise ValueError(f"Invalid scan mode: {profile.mode}")
   42: 
   43:     if profile.x_min >= profile.x_max:
   44:         raise ValueError("x_min must be smaller than x_max")
   45: 
   46:     if profile.y_min >= profile.y_max:
   47:         raise ValueError("y_min must be smaller than y_max")
```

### Context around line 73

```python
   69: 
   70:     if not (limits.y_min <= profile.y_max <= limits.y_max):
   71:         raise ValueError("y_max is outside motion limits")
   72: 
>> 73:     if not (limits.z_min <= profile.z <= limits.z_max):
   74:         raise ValueError("z is outside motion limits")
   75: 
   76:     if profile.feedrate_xy <= 0:
   77:         raise ValueError("feedrate_xy must be positive")
   78: 
   79:     if profile.feedrate_z <= 0:
   80:         raise ValueError("feedrate_z must be positive")
```

## Backend move_to Z handling

File: `core\motion\prusa_gcode_backend.py`


### Context around line 44

```python
   40:         self.y_limits = y_limits
   41:         self.z_limits = z_limits
   42:         self._ser = None
   43:         self._connected = False
>> 44:         self._last_position: Dict[str, float] = {}
   45:         self._last_state: Dict = {"connected": False, "position": {}}
   46: 
   47:     # -------------------------
   48:     # low-level helpers
   49:     # -------------------------
   50:     def _require_serial(self) -> None:
   51:         if serial is None:
   52:             raise RuntimeError("pyserial is not installed. Run: python -m pip install pyserial")
```

### Context around line 96

```python
   92:             if m:
   93:                 out[axis.lower()] = float(m.group(1))
   94:         return out
   95: 
>> 96:     def _check_limits(self, *, x: Optional[float], y: Optional[float], z: Optional[float]) -> None:
   97:         checks = (
   98:             ("X", x, self.x_limits),
   99:             ("Y", y, self.y_limits),
   100:             ("Z", z, self.z_limits),
   101:         )
   102:         for axis, value, limits in checks:
   103:             if value is None or limits is None:
   104:                 continue
```

### Context around line 171

```python
   167:         self._last_state = {
   168:             "connected": True,
   169:             "port": self.port,
   170:             "baudrate": self.baudrate,
>> 171:             "position": dict(self._last_position),
   172:         }
   173: 
   174:         # Safe: absolute mode only, no motion
   175:         try:
   176:             self.send_gcode("G90", timeout=2.0)
   177:         except Exception:
   178:             # Some firmwares may respond differently; don't fail hard here.
   179:             pass
```

### Context around line 186

```python
   182:         try:
   183:             lines = self.send_gcode("M114", timeout=2.5)
   184:             parsed = self._parse_m114(lines)
   185:             if parsed:
>> 186:                 self._last_position.update(parsed)
   187:         except Exception:
   188:             pass
   189: 
   190:         self._last_state["position"] = dict(self._last_position)
   191: 
   192:     def disconnect(self) -> None:
   193:         if self._ser is not None:
   194:             try:
```

### Context around line 190

```python
   186:                 self._last_position.update(parsed)
   187:         except Exception:
   188:             pass
   189: 
>> 190:         self._last_state["position"] = dict(self._last_position)
   191: 
   192:     def disconnect(self) -> None:
   193:         if self._ser is not None:
   194:             try:
   195:                 self._ser.close()
   196:             except Exception:
   197:                 pass
   198:         self._ser = None
```

### Context around line 200

```python
   196:             except Exception:
   197:                 pass
   198:         self._ser = None
   199:         self._connected = False
>> 200:         self._last_state = {"connected": False, "position": dict(self._last_position)}
   201: 
   202:     def home(self) -> None:
   203:         # This WILL move the printer. Keep as explicit call.
   204:         self.send_gcode("G28", timeout=30.0)
   205:         try:
   206:             lines = self.send_gcode("M114", timeout=3.0)
   207:             parsed = self._parse_m114(lines)
   208:             if parsed:
```

### Context around line 209

```python
   205:         try:
   206:             lines = self.send_gcode("M114", timeout=3.0)
   207:             parsed = self._parse_m114(lines)
   208:             if parsed:
>> 209:                 self._last_position.update(parsed)
   210:         except Exception:
   211:             pass
   212:         self._last_state["position"] = dict(self._last_position)
   213: 
   214:     def move_to(
   215:         self,
   216:         *,
   217:         x: Optional[float] = None,
```

### Context around line 212

```python
   208:             if parsed:
   209:                 self._last_position.update(parsed)
   210:         except Exception:
   211:             pass
>> 212:         self._last_state["position"] = dict(self._last_position)
   213: 
   214:     def move_to(
   215:         self,
   216:         *,
   217:         x: Optional[float] = None,
   218:         y: Optional[float] = None,
   219:         z: Optional[float] = None,
   220:         feedrate: Optional[float] = None,
```

### Context around line 214

```python
   210:         except Exception:
   211:             pass
   212:         self._last_state["position"] = dict(self._last_position)
   213: 
>> 214:     def move_to(
   215:         self,
   216:         *,
   217:         x: Optional[float] = None,
   218:         y: Optional[float] = None,
   219:         z: Optional[float] = None,
   220:         feedrate: Optional[float] = None,
   221:     ) -> None:
   222:         # This WILL move the printer. Keep as explicit call.
```

### Context around line 226

```python
   222:         # This WILL move the printer. Keep as explicit call.
   223:         if x is None and y is None and z is None:
   224:             raise ValueError("move_to requires at least one axis target (x, y, or z).")
   225: 
>> 226:         self._check_limits(x=x, y=y, z=z)
   227: 
   228:         parts = ["G1"]
   229:         if x is not None:
   230:             parts.append(f"X{x}")
   231:         if y is not None:
   232:             parts.append(f"Y{y}")
   233:         if z is not None:
   234:             parts.append(f"Z{z}")
```

### Context around line 233

```python
   229:         if x is not None:
   230:             parts.append(f"X{x}")
   231:         if y is not None:
   232:             parts.append(f"Y{y}")
>> 233:         if z is not None:
   234:             parts.append(f"Z{z}")
   235:         if feedrate is not None:
   236:             parts.append(f"F{feedrate}")
   237:         cmd = " ".join(parts)
   238:         self.send_gcode(cmd, timeout=30.0)
   239: 
   240:         if x is not None:
   241:             self._last_position["x"] = float(x)
```

### Context around line 234

```python
   230:             parts.append(f"X{x}")
   231:         if y is not None:
   232:             parts.append(f"Y{y}")
   233:         if z is not None:
>> 234:             parts.append(f"Z{z}")
   235:         if feedrate is not None:
   236:             parts.append(f"F{feedrate}")
   237:         cmd = " ".join(parts)
   238:         self.send_gcode(cmd, timeout=30.0)
   239: 
   240:         if x is not None:
   241:             self._last_position["x"] = float(x)
   242:         if y is not None:
```

## Possible 60 mm source locations

- `core\application\gui_scan_launcher.py`:54: from core.motion.parking import park_mk4s
- `core\application\gui_scan_launcher.py`:322: self.park_btn = QPushButton("PARK MK4S")
- `core\application\gui_scan_launcher.py`:323: self.park_btn.clicked.connect(self.park_workstation)
- `core\application\gui_scan_launcher.py`:550: hardware_layout.addWidget(self.park_btn)
- `core\application\gui_scan_launcher.py`:824: "Measurement safety rule: initialize once, approach Z, scan, then safe-park Z before XY and close.",
- `core\application\gui_scan_launcher.py`:920: parking = self.config["parking_position"]
- `core\application\gui_scan_launcher.py`:936: "8. Use **POWER OFF / SAFE PARK** before closing.\n\n"
- `core\application\gui_scan_launcher.py`:942: f"- Power-off parking sequence: Z -> {parking['z']} first, then X/Y -> {parking['x']}/{parking['y']}.\n"
- `core\application\gui_scan_launcher.py`:944: "- The normal close action is locked until power-off/safe-park completes.\n"
- `core\application\gui_scan_launcher.py`:1060: xy_speed_mm_s = xy_feedrate / 60.0
- `core\application\gui_scan_launcher.py`:1153: self.park_btn.setEnabled(enabled)
- `core\application\gui_scan_launcher.py`:1319: def park_workstation(self) -> bool:
- `core\application\gui_scan_launcher.py`:1320: if not self.require_initialized("Park MK4S"):
- `core\application\gui_scan_launcher.py`:1323: parking = self.config["parking_position"]
- `core\application\gui_scan_launcher.py`:1325: "Park MK4S",
- `core\application\gui_scan_launcher.py`:1327: "Move MK4S to workstation park position?\n\n"
- `core\application\gui_scan_launcher.py`:1328: f"Sequence: Z -> {parking['z']} first, then X/Y -> {parking['x']}/{parking['y']}.\n\n"
- `core\application\gui_scan_launcher.py`:1332: self.append_log("[PARK] Park cancelled by operator")
- `core\application\gui_scan_launcher.py`:1336: state = park_mk4s(self.config)
- `core\application\gui_scan_launcher.py`:1338: self.append_log(f"[PARK] Park failed: {error}")
- `core\application\gui_scan_launcher.py`:1341: "Park failed",
- `core\application\gui_scan_launcher.py`:1342: f"MK4S parking failed:\n\n{error}",
- `core\application\gui_scan_launcher.py`:1347: self.update_position_display(position, "parked")
- `core\application\gui_scan_launcher.py`:1348: self.append_log(f"[PARK] MK4S parked: {state}")
- `core\application\gui_scan_launcher.py`:1353: parking = self.config["parking_position"]
- `core\application\gui_scan_launcher.py`:1355: "Power off / safe park",
- `core\application\gui_scan_launcher.py`:1358: f"Parking sequence: Z -> {parking['z']} first, then X/Y -> {parking['x']}/{parking['y']}.\n"
- `core\application\gui_scan_launcher.py`:1359: f"Full sequence: disable real motion, disconnect dry-run Z, move Z -> {parking['z']}, "
- `core\application\gui_scan_launcher.py`:1360: f"then X/Y -> {parking['x']}/{parking['y']}.\n\n"
- `core\application\gui_scan_launcher.py`:1380: state = park_mk4s(self.config)
- `core\application\gui_scan_launcher.py`:1384: self.append_log(f"[POWER OFF] Safe park failed: {error}")
- `core\application\gui_scan_launcher.py`:1388: f"MK4S safe park failed. The software will remain open.\n\n{error}",
- `core\application\gui_scan_launcher.py`:1392: self.update_position_display(state.get("position", {}), "power-off safe park")
- `core\application\gui_scan_launcher.py`:1393: self.append_log(f"[POWER OFF] MK4S safe park complete: {state}")
- `core\application\gui_scan_launcher.py`:1400: self.hardware_status_label.setText("Hardware / System Connection: POWERED OFF / SAFE PARK COMPLETE")
- `core\application\gui_scan_launcher.py`:1412: "Use POWER OFF / SAFE PARK before closing the software.",
- `core\application\gui_scan_launcher.py`:1559: "Live scan complete: Z retracted to safe setpoint and XY return/park is ready for the shutdown sequence."
- `core\application\gui_scan_launcher.py`:2589: "Current step: real motion disabled. You can adjust settings, dry-run again, park, or close safely."
- `core\application\gui_scan_launcher.py`:2642: "Current step: hardware scan completed and safe park requested. Inspect output before deinitializing."
- `core\application\gui_scan_launcher.py`:2645: state = park_mk4s(self.config)
- `core\application\gui_scan_launcher.py`:2646: self.update_position_display(state.get("position", {}), "post-scan safe park")
- `core\application\gui_scan_launcher.py`:2648: self.append_log(f"[HARDWARE] Post-scan safe park complete: {state}")
- `core\application\gui_scan_launcher.py`:2650: self.append_log(f"[HARDWARE] Post-scan safe park failed: {error}")
- `core\application\gui_scan_launcher.py`:2653: "Post-scan safe park failed",
- `core\application\gui_scan_launcher.py`:2654: f"Scan completed, but safe park failed. Keep the software open and recover manually.\n\n{error}",
- `core\application\gui_scan_launcher.py`:2691: "Close is locked until POWER OFF / SAFE PARK completes.\n\n"
- `core\application\gui_scan_launcher.py`:2693: "and safe park before the software exits."
- `core\application\gui_scan_launcher.py`:2696: self.append_log("[GUI] Close blocked: power-off/safe-park required")
- `core\application\hardware_test_console_gui.py`:346: elif assessment.score >= 60:
- `core\education\config_loader.py`:72: def get_parking_position(config):
- `core\education\config_loader.py`:73: """Extract the safe workstation parking position."""
- `core\education\config_loader.py`:74: return config["parking_position"]
- `core\motion\parking.py`:3: from core.education.config_loader import get_parking_position, get_prusa_backend_kwargs
- `core\motion\parking.py`:7: def park_mk4s(config: dict) -> dict:
- `core\motion\parking.py`:8: """Park MK4S by retracting Z first, then moving XY to the parking corner."""
- `core\motion\parking.py`:9: parking = get_parking_position(config)
- `core\motion\parking.py`:15: backend.move_to(z=float(parking["z"]), feedrate=feedrates["z"])
- `core\motion\parking.py`:17: x=float(parking["x"]),
- `core\motion\parking.py`:18: y=float(parking["y"]),
- `core\system\hardware_test_controls.py`:35: DEFAULT_Z_FEEDRATE = 300.0
- `core\system\hardware_test_controls.py`:88: [f"G1 Z{SAFE_RETRACT_Z:.2f} F{DEFAULT_Z_FEEDRATE:.0f}", "M400", "M114"],
- `core\system\hardware_test_controls.py`:97: f"G1 Z{SAFE_RETRACT_Z:.2f} F{DEFAULT_Z_FEEDRATE:.0f}",
- `core\system\hardware_test_controls.py`:112: "Z_STEP_UP": ("z", step_mm, DEFAULT_Z_FEEDRATE),
- `core\system\hardware_test_controls.py`:113: "Z_STEP_DOWN": ("z", -step_mm, DEFAULT_Z_FEEDRATE),
- `core\system\hardware_test_controls.py`:191: backend.move_to(z=SAFE_RETRACT_Z, feedrate=DEFAULT_Z_FEEDRATE)
- `core\system\hardware_test_controls.py`:192: backend.send_gcode("M400", timeout=60.0)
- `core\system\hardware_test_controls.py`:195: backend.move_to(z=SAFE_RETRACT_Z, feedrate=DEFAULT_Z_FEEDRATE)
- `core\system\hardware_test_controls.py`:196: backend.send_gcode("M400", timeout=60.0)
- `core\system\hardware_test_controls.py`:198: backend.send_gcode("M400", timeout=60.0)
- `core\system\hardware_test_controls.py`:204: kwargs = {axis: value, "feedrate": DEFAULT_Z_FEEDRATE if axis == "z" else DEFAULT_XY_FEEDRATE}
- `core\system\hardware_test_controls.py`:206: backend.send_gcode("M400", timeout=60.0)
- `core\system\mk4s_z_auto_approach.py`:68: steps = [110.0, 100.0, 90.0, 80.0, 70.0, 60.0]
- `core\system\mk4s_z_auto_approach.py`:69: current = 60.0
- `core\system\mk4s_z_auto_approach.py`:200: lines = _read_until_ok(ser, timeout_s=60.0 if gcode in {command, "M400"} else 8.0)
- `core\system\mk4s_z_auto_approach.py`:214: safe_z = float(reference["safe_retract_z"])
- `core\system\mk4s_z_auto_approach.py`:215: command = f"G1 Z{safe_z:.2f} F600"
- `core\system\mk4s_z_auto_approach.py`:221: target_z=safe_z,
- `core\system\mk4s_z_auto_approach.py`:231: lines = _read_until_ok(ser, timeout_s=60.0 if gcode in {command, "M400"} else 8.0)
- `core\system\mk4s_z_auto_approach.py`:237: target_z=safe_z,
- `core\system\mk4s_z_auto_approach.py`:238: message=f"Z safe retract complete. Target Z={safe_z:.2f}",