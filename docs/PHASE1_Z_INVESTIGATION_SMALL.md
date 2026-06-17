# Phase 1 Z Investigation Small Report

Purpose: find where GUI Z input becomes ScanProfile.z and where hardware Z movement is generated.

## GUI likely Z inputs and spin boxes

File: core\application\gui_scan_launcher.py


### Around line 51

46:     validate_scan_profile,
47:     MAX_SCAN_RESOLUTION,
48: )
49: from core.system.hardware_diagnostics import run_hardware_communication_report
50: from core.system.hardware_profile import SPMHardwareProfile
51: from core.system.mk4s_z_auto_approach import run_mk4s_z_auto_approach, run_mk4s_z_manual_step, run_mk4s_z_safe_retract
52: from core.system.workstation_initializer import run_workstation_initialization
53: from core.motion.prusa_gcode_backend import PrusaGcodeBackend
54: from core.motion.parking import park_mk4s
55: 
56: from core.z_control.crtouch_probe_plan import CRTouchProbePlan
57: from core.z_control.z_driver_arduino_safe import ZDriverArduino
58: 
59: 

### Around line 56

51: from core.system.mk4s_z_auto_approach import run_mk4s_z_auto_approach, run_mk4s_z_manual_step, run_mk4s_z_safe_retract
52: from core.system.workstation_initializer import run_workstation_initialization
53: from core.motion.prusa_gcode_backend import PrusaGcodeBackend
54: from core.motion.parking import park_mk4s
55: 
56: from core.z_control.crtouch_probe_plan import CRTouchProbePlan
57: from core.z_control.z_driver_arduino_safe import ZDriverArduino
58: 
59: 
60: # ============================================================
61: # SPM Educational GUI
62: # Safe GUI wrapper around the verified CLI scan launcher
63: # ============================================================
64: APP_VERSION = "v0.25.0"

### Around line 57

52: from core.system.workstation_initializer import run_workstation_initialization
53: from core.motion.prusa_gcode_backend import PrusaGcodeBackend
54: from core.motion.parking import park_mk4s
55: 
56: from core.z_control.crtouch_probe_plan import CRTouchProbePlan
57: from core.z_control.z_driver_arduino_safe import ZDriverArduino
58: 
59: 
60: # ============================================================
61: # SPM Educational GUI
62: # Safe GUI wrapper around the verified CLI scan launcher
63: # ============================================================
64: APP_VERSION = "v0.25.0"
65: APP_PHASE = "Focused SPM Workflow - Connection, Approach, Measurement"

### Around line 93

88:         self.last_plot_path = ""
89:         self.scan_viewers = []
90:         self.direction_viewers = {}
91:         self.direction_preview_labels = {}
92:         self.direction_window_labels = {}
93:         self.z_approached = False
94:         self.scan_stop_requested = False
95:         self.scan_pause_requested = False
96:         self.live_scan_timer = QTimer(self)
97:         self.live_scan_timer.timeout.connect(self.advance_live_scan)
98:         self.live_scan_points = []
99:         self.live_scan_index = 0
100:         self.live_scan_rows = []
101:         self.live_scan_current_line = []

### Around line 104

99:         self.live_scan_index = 0
100:         self.live_scan_rows = []
101:         self.live_scan_current_line = []
102:         self.live_scan_profile = None
103:         self.live_scan_active = False
104:         self.live_scan_z_setpoint = float(self.config["scan_area"]["z"])
105: 
106:         # ------------------------------------------------------------
107:         # Locked motion limits
108:         # ------------------------------------------------------------
109:         self.limits = MotionLimits(
110:             x_min=self.config["motion_limits"]["x"][0],
111:             x_max=self.config["motion_limits"]["x"][1],
112:             y_min=self.config["motion_limits"]["y"][0],

### Around line 114

109:         self.limits = MotionLimits(
110:             x_min=self.config["motion_limits"]["x"][0],
111:             x_max=self.config["motion_limits"]["x"][1],
112:             y_min=self.config["motion_limits"]["y"][0],
113:             y_max=self.config["motion_limits"]["y"][1],
114:             z_min=self.config["motion_limits"]["z"][0],
115:             z_max=self.config["motion_limits"]["z"][1],
116:         )
117: 
118:         scan_area = self.config["scan_area"]
119: 
120:         # ------------------------------------------------------------
121:         # Layouts
122:         # ------------------------------------------------------------

### Around line 115

110:             x_min=self.config["motion_limits"]["x"][0],
111:             x_max=self.config["motion_limits"]["x"][1],
112:             y_min=self.config["motion_limits"]["y"][0],
113:             y_max=self.config["motion_limits"]["y"][1],
114:             z_min=self.config["motion_limits"]["z"][0],
115:             z_max=self.config["motion_limits"]["z"][1],
116:         )
117: 
118:         scan_area = self.config["scan_area"]
119: 
120:         # ------------------------------------------------------------
121:         # Layouts
122:         # ------------------------------------------------------------
123:         main_layout = QVBoxLayout()

### Around line 133

128:         # ------------------------------------------------------------
129:         self.x_min = QLineEdit(str(scan_area["x_min"]))
130:         self.x_max = QLineEdit(str(scan_area["x_max"]))
131:         self.y_min = QLineEdit(str(scan_area["y_min"]))
132:         self.y_max = QLineEdit(str(scan_area["y_max"]))
133:         self.z = QLineEdit(str(scan_area["z"]))
134:         self.x_res = QLineEdit(str(scan_area["x_resolution"]))
135:         self.y_res = QLineEdit(str(scan_area["y_resolution"]))
136:         self.xy_feedrate = QLineEdit(str(self.safe_feedrates["xy"]))
137:         self.z_feedrate = QLineEdit(str(self.safe_feedrates["z"]))
138:         self.z_dwell_ms = QLineEdit("50")
139:         self.line_time_estimate_label = QLabel("Line time: waiting for scan settings")
140:         self.frame_time_estimate_label = QLabel("Frame time: waiting for scan settings")
141:         self.mode_readiness_label = QLabel("")

### Around line 137

132:         self.y_max = QLineEdit(str(scan_area["y_max"]))
133:         self.z = QLineEdit(str(scan_area["z"]))
134:         self.x_res = QLineEdit(str(scan_area["x_resolution"]))
135:         self.y_res = QLineEdit(str(scan_area["y_resolution"]))
136:         self.xy_feedrate = QLineEdit(str(self.safe_feedrates["xy"]))
137:         self.z_feedrate = QLineEdit(str(self.safe_feedrates["z"]))
138:         self.z_dwell_ms = QLineEdit("50")
139:         self.line_time_estimate_label = QLabel("Line time: waiting for scan settings")
140:         self.frame_time_estimate_label = QLabel("Frame time: waiting for scan settings")
141:         self.mode_readiness_label = QLabel("")
142:         self.mode_readiness_label.setWordWrap(True)
143: 
144:         # ------------------------------------------------------------
145:         # Output CSV path

### Around line 138

133:         self.z = QLineEdit(str(scan_area["z"]))
134:         self.x_res = QLineEdit(str(scan_area["x_resolution"]))
135:         self.y_res = QLineEdit(str(scan_area["y_resolution"]))
136:         self.xy_feedrate = QLineEdit(str(self.safe_feedrates["xy"]))
137:         self.z_feedrate = QLineEdit(str(self.safe_feedrates["z"]))
138:         self.z_dwell_ms = QLineEdit("50")
139:         self.line_time_estimate_label = QLabel("Line time: waiting for scan settings")
140:         self.frame_time_estimate_label = QLabel("Frame time: waiting for scan settings")
141:         self.mode_readiness_label = QLabel("")
142:         self.mode_readiness_label.setWordWrap(True)
143: 
144:         # ------------------------------------------------------------
145:         # Output CSV path
146:         # ------------------------------------------------------------

### Around line 195

190: 
191:         self.open_scan_setup_btn = QPushButton("MEASUREMENT SETUP")
192:         self.open_scan_setup_btn.clicked.connect(self.open_measurement_window)
193:         self.open_xy_scanner_btn = QPushButton("XY SCANNER")
194:         self.open_xy_scanner_btn.clicked.connect(self.open_xy_scanner_window)
195:         self.open_z_regulation_btn = QPushButton("SERVICE APPROACH")
196:         self.open_z_regulation_btn.clicked.connect(self.open_z_regulation_window)
197:         self.open_hardware_tools_btn = QPushButton("HARDWARE CHECK")
198:         self.open_hardware_tools_btn.clicked.connect(self.open_hardware_tools_window)
199:         self.hardware_check_btn = QPushButton("RUN HARDWARE CHECK")
200:         self.hardware_check_btn.clicked.connect(self.run_hardware_check_only)
201:         self.open_z_tools_btn = QPushButton("Z / APPROACH")
202:         self.open_z_tools_btn.clicked.connect(self.open_measurement_window)
203:         self.about_btn = QPushButton("ABOUT")

### Around line 196

191:         self.open_scan_setup_btn = QPushButton("MEASUREMENT SETUP")
192:         self.open_scan_setup_btn.clicked.connect(self.open_measurement_window)
193:         self.open_xy_scanner_btn = QPushButton("XY SCANNER")
194:         self.open_xy_scanner_btn.clicked.connect(self.open_xy_scanner_window)
195:         self.open_z_regulation_btn = QPushButton("SERVICE APPROACH")
196:         self.open_z_regulation_btn.clicked.connect(self.open_z_regulation_window)
197:         self.open_hardware_tools_btn = QPushButton("HARDWARE CHECK")
198:         self.open_hardware_tools_btn.clicked.connect(self.open_hardware_tools_window)
199:         self.hardware_check_btn = QPushButton("RUN HARDWARE CHECK")
200:         self.hardware_check_btn.clicked.connect(self.run_hardware_check_only)
201:         self.open_z_tools_btn = QPushButton("Z / APPROACH")
202:         self.open_z_tools_btn.clicked.connect(self.open_measurement_window)
203:         self.about_btn = QPushButton("ABOUT")
204:         self.about_btn.clicked.connect(self.show_about)

## GUI ScanProfile creation / scan start

File: core\application\gui_scan_launcher.py


### Around line 42

37: from PyQt5.QtCore import Qt, QTimer
38: 
39: from core.acquisition.raster_stream import load_raster_frame
40: from core.application.workstation_status import WorkstationStatus
41: from core.education.config_loader import load_config, get_safe_feedrates, get_scan_mode_preset
42: from core.education.scan_profile import (
43:     ScanProfile,
44:     MotionLimits,
45:     VALID_SCAN_MODES,
46:     validate_scan_profile,
47:     MAX_SCAN_RESOLUTION,
48: )
49: from core.system.hardware_diagnostics import run_hardware_communication_report
50: from core.system.hardware_profile import SPMHardwareProfile

### Around line 43

38: 
39: from core.acquisition.raster_stream import load_raster_frame
40: from core.application.workstation_status import WorkstationStatus
41: from core.education.config_loader import load_config, get_safe_feedrates, get_scan_mode_preset
42: from core.education.scan_profile import (
43:     ScanProfile,
44:     MotionLimits,
45:     VALID_SCAN_MODES,
46:     validate_scan_profile,
47:     MAX_SCAN_RESOLUTION,
48: )
49: from core.system.hardware_diagnostics import run_hardware_communication_report
50: from core.system.hardware_profile import SPMHardwareProfile
51: from core.system.mk4s_z_auto_approach import run_mk4s_z_auto_approach, run_mk4s_z_manual_step, run_mk4s_z_safe_retract

### Around line 46

41: from core.education.config_loader import load_config, get_safe_feedrates, get_scan_mode_preset
42: from core.education.scan_profile import (
43:     ScanProfile,
44:     MotionLimits,
45:     VALID_SCAN_MODES,
46:     validate_scan_profile,
47:     MAX_SCAN_RESOLUTION,
48: )
49: from core.system.hardware_diagnostics import run_hardware_communication_report
50: from core.system.hardware_profile import SPMHardwareProfile
51: from core.system.mk4s_z_auto_approach import run_mk4s_z_auto_approach, run_mk4s_z_manual_step, run_mk4s_z_safe_retract
52: from core.system.workstation_initializer import run_workstation_initialization
53: from core.motion.prusa_gcode_backend import PrusaGcodeBackend
54: from core.motion.parking import park_mk4s

### Around line 50

45:     VALID_SCAN_MODES,
46:     validate_scan_profile,
47:     MAX_SCAN_RESOLUTION,
48: )
49: from core.system.hardware_diagnostics import run_hardware_communication_report
50: from core.system.hardware_profile import SPMHardwareProfile
51: from core.system.mk4s_z_auto_approach import run_mk4s_z_auto_approach, run_mk4s_z_manual_step, run_mk4s_z_safe_retract
52: from core.system.workstation_initializer import run_workstation_initialization
53: from core.motion.prusa_gcode_backend import PrusaGcodeBackend
54: from core.motion.parking import park_mk4s
55: 
56: from core.z_control.crtouch_probe_plan import CRTouchProbePlan
57: from core.z_control.z_driver_arduino_safe import ZDriverArduino
58: 

### Around line 85

80:         # ------------------------------------------------------------
81:         self.config = load_config()
82:         self.safe_feedrates = get_safe_feedrates(self.config)
83:         self.workstation_status = WorkstationStatus.from_config(self.config)
84:         self.crtouch_plan = CRTouchProbePlan()
85:         self.hardware_profile = SPMHardwareProfile.from_config(self.config)
86:         self.current_position = {"x": None, "y": None, "z": None}
87:         self.shutdown_complete = False
88:         self.last_plot_path = ""
89:         self.scan_viewers = []
90:         self.direction_viewers = {}
91:         self.direction_preview_labels = {}
92:         self.direction_window_labels = {}
93:         self.z_approached = False

### Around line 102

97:         self.live_scan_timer.timeout.connect(self.advance_live_scan)
98:         self.live_scan_points = []
99:         self.live_scan_index = 0
100:         self.live_scan_rows = []
101:         self.live_scan_current_line = []
102:         self.live_scan_profile = None
103:         self.live_scan_active = False
104:         self.live_scan_z_setpoint = float(self.config["scan_area"]["z"])
105: 
106:         # ------------------------------------------------------------
107:         # Locked motion limits
108:         # ------------------------------------------------------------
109:         self.limits = MotionLimits(
110:             x_min=self.config["motion_limits"]["x"][0],

### Around line 149

144:         # ------------------------------------------------------------
145:         # Output CSV path
146:         # ------------------------------------------------------------
147:         self.output_file = QLineEdit("data/interface_test_output.csv")
148: 
149:         form_layout.addRow("X min:", self.field_with_tip(self.x_min, self.hardware_profile.compact_axis_range("X")))
150:         form_layout.addRow("X max:", self.field_with_tip(self.x_max, self.hardware_profile.compact_axis_range("X")))
151:         form_layout.addRow("Y min:", self.field_with_tip(self.y_min, self.hardware_profile.compact_axis_range("Y")))
152:         form_layout.addRow("Y max:", self.field_with_tip(self.y_max, self.hardware_profile.compact_axis_range("Y")))
153:         form_layout.addRow("X resolution:", self.field_with_tip(self.x_res, self.hardware_profile.compact_resolution_range()))
154:         form_layout.addRow("Y resolution:", self.field_with_tip(self.y_res, self.hardware_profile.compact_resolution_range()))
155:         form_layout.addRow("XY speed mm/min:", self.xy_feedrate)
156:         form_layout.addRow("Line estimate:", self.line_time_estimate_label)
157:         form_layout.addRow("Frame estimate:", self.frame_time_estimate_label)

### Around line 150

145:         # Output CSV path
146:         # ------------------------------------------------------------
147:         self.output_file = QLineEdit("data/interface_test_output.csv")
148: 
149:         form_layout.addRow("X min:", self.field_with_tip(self.x_min, self.hardware_profile.compact_axis_range("X")))
150:         form_layout.addRow("X max:", self.field_with_tip(self.x_max, self.hardware_profile.compact_axis_range("X")))
151:         form_layout.addRow("Y min:", self.field_with_tip(self.y_min, self.hardware_profile.compact_axis_range("Y")))
152:         form_layout.addRow("Y max:", self.field_with_tip(self.y_max, self.hardware_profile.compact_axis_range("Y")))
153:         form_layout.addRow("X resolution:", self.field_with_tip(self.x_res, self.hardware_profile.compact_resolution_range()))
154:         form_layout.addRow("Y resolution:", self.field_with_tip(self.y_res, self.hardware_profile.compact_resolution_range()))
155:         form_layout.addRow("XY speed mm/min:", self.xy_feedrate)
156:         form_layout.addRow("Line estimate:", self.line_time_estimate_label)
157:         form_layout.addRow("Frame estimate:", self.frame_time_estimate_label)
158:         form_layout.addRow("Output CSV:", self.output_file)

### Around line 151

146:         # ------------------------------------------------------------
147:         self.output_file = QLineEdit("data/interface_test_output.csv")
148: 
149:         form_layout.addRow("X min:", self.field_with_tip(self.x_min, self.hardware_profile.compact_axis_range("X")))
150:         form_layout.addRow("X max:", self.field_with_tip(self.x_max, self.hardware_profile.compact_axis_range("X")))
151:         form_layout.addRow("Y min:", self.field_with_tip(self.y_min, self.hardware_profile.compact_axis_range("Y")))
152:         form_layout.addRow("Y max:", self.field_with_tip(self.y_max, self.hardware_profile.compact_axis_range("Y")))
153:         form_layout.addRow("X resolution:", self.field_with_tip(self.x_res, self.hardware_profile.compact_resolution_range()))
154:         form_layout.addRow("Y resolution:", self.field_with_tip(self.y_res, self.hardware_profile.compact_resolution_range()))
155:         form_layout.addRow("XY speed mm/min:", self.xy_feedrate)
156:         form_layout.addRow("Line estimate:", self.line_time_estimate_label)
157:         form_layout.addRow("Frame estimate:", self.frame_time_estimate_label)
158:         form_layout.addRow("Output CSV:", self.output_file)
159: 

### Around line 152

147:         self.output_file = QLineEdit("data/interface_test_output.csv")
148: 
149:         form_layout.addRow("X min:", self.field_with_tip(self.x_min, self.hardware_profile.compact_axis_range("X")))
150:         form_layout.addRow("X max:", self.field_with_tip(self.x_max, self.hardware_profile.compact_axis_range("X")))
151:         form_layout.addRow("Y min:", self.field_with_tip(self.y_min, self.hardware_profile.compact_axis_range("Y")))
152:         form_layout.addRow("Y max:", self.field_with_tip(self.y_max, self.hardware_profile.compact_axis_range("Y")))
153:         form_layout.addRow("X resolution:", self.field_with_tip(self.x_res, self.hardware_profile.compact_resolution_range()))
154:         form_layout.addRow("Y resolution:", self.field_with_tip(self.y_res, self.hardware_profile.compact_resolution_range()))
155:         form_layout.addRow("XY speed mm/min:", self.xy_feedrate)
156:         form_layout.addRow("Line estimate:", self.line_time_estimate_label)
157:         form_layout.addRow("Frame estimate:", self.frame_time_estimate_label)
158:         form_layout.addRow("Output CSV:", self.output_file)
159: 
160:         # ------------------------------------------------------------

### Around line 153

148: 
149:         form_layout.addRow("X min:", self.field_with_tip(self.x_min, self.hardware_profile.compact_axis_range("X")))
150:         form_layout.addRow("X max:", self.field_with_tip(self.x_max, self.hardware_profile.compact_axis_range("X")))
151:         form_layout.addRow("Y min:", self.field_with_tip(self.y_min, self.hardware_profile.compact_axis_range("Y")))
152:         form_layout.addRow("Y max:", self.field_with_tip(self.y_max, self.hardware_profile.compact_axis_range("Y")))
153:         form_layout.addRow("X resolution:", self.field_with_tip(self.x_res, self.hardware_profile.compact_resolution_range()))
154:         form_layout.addRow("Y resolution:", self.field_with_tip(self.y_res, self.hardware_profile.compact_resolution_range()))
155:         form_layout.addRow("XY speed mm/min:", self.xy_feedrate)
156:         form_layout.addRow("Line estimate:", self.line_time_estimate_label)
157:         form_layout.addRow("Frame estimate:", self.frame_time_estimate_label)
158:         form_layout.addRow("Output CSV:", self.output_file)
159: 
160:         # ------------------------------------------------------------
161:         # Browse button for CSV output

### Around line 154

149:         form_layout.addRow("X min:", self.field_with_tip(self.x_min, self.hardware_profile.compact_axis_range("X")))
150:         form_layout.addRow("X max:", self.field_with_tip(self.x_max, self.hardware_profile.compact_axis_range("X")))
151:         form_layout.addRow("Y min:", self.field_with_tip(self.y_min, self.hardware_profile.compact_axis_range("Y")))
152:         form_layout.addRow("Y max:", self.field_with_tip(self.y_max, self.hardware_profile.compact_axis_range("Y")))
153:         form_layout.addRow("X resolution:", self.field_with_tip(self.x_res, self.hardware_profile.compact_resolution_range()))
154:         form_layout.addRow("Y resolution:", self.field_with_tip(self.y_res, self.hardware_profile.compact_resolution_range()))
155:         form_layout.addRow("XY speed mm/min:", self.xy_feedrate)
156:         form_layout.addRow("Line estimate:", self.line_time_estimate_label)
157:         form_layout.addRow("Frame estimate:", self.frame_time_estimate_label)
158:         form_layout.addRow("Output CSV:", self.output_file)
159: 
160:         # ------------------------------------------------------------
161:         # Browse button for CSV output
162:         # ------------------------------------------------------------

## ScanProfile definition and validation

File: core\education\scan_profile.py


### Around line 10

5: class MotionLimits:
6:     x_min: float
7:     x_max: float
8:     y_min: float
9:     y_max: float
10:     z_min: float
11:     z_max: float
12: 
13: 
14: @dataclass(frozen=True)
15: class ScanProfile:
16:     x_min: float
17:     x_max: float
18:     y_min: float

### Around line 11

6:     x_min: float
7:     x_max: float
8:     y_min: float
9:     y_max: float
10:     z_min: float
11:     z_max: float
12: 
13: 
14: @dataclass(frozen=True)
15: class ScanProfile:
16:     x_min: float
17:     x_max: float
18:     y_min: float
19:     y_max: float

### Around line 15

10:     z_min: float
11:     z_max: float
12: 
13: 
14: @dataclass(frozen=True)
15: class ScanProfile:
16:     x_min: float
17:     x_max: float
18:     y_min: float
19:     y_max: float
20:     z: float
21:     x_resolution: int
22:     y_resolution: int
23:     feedrate_xy: float

### Around line 20

15: class ScanProfile:
16:     x_min: float
17:     x_max: float
18:     y_min: float
19:     y_max: float
20:     z: float
21:     x_resolution: int
22:     y_resolution: int
23:     feedrate_xy: float
24:     feedrate_z: float
25:     mode: str = "SIMULATED_SURFACE"
26: 
27: 
28: VALID_SCAN_MODES = {

### Around line 24

19:     y_max: float
20:     z: float
21:     x_resolution: int
22:     y_resolution: int
23:     feedrate_xy: float
24:     feedrate_z: float
25:     mode: str = "SIMULATED_SURFACE"
26: 
27: 
28: VALID_SCAN_MODES = {
29:     "SIMULATED_SURFACE",
30:     "CONTACT_PROBE",
31:     "AFM_CONTACT",
32:     "STM_DEMO",

### Around line 39

34: 
35: 
36: MAX_SCAN_RESOLUTION = 250
37: 
38: 
39: def validate_scan_profile(profile: ScanProfile, limits: MotionLimits) -> None:
40:     if profile.mode not in VALID_SCAN_MODES:
41:         raise ValueError(f"Invalid scan mode: {profile.mode}")
42: 
43:     if profile.x_min >= profile.x_max:
44:         raise ValueError("x_min must be smaller than x_max")
45: 
46:     if profile.y_min >= profile.y_max:
47:         raise ValueError("y_min must be smaller than y_max")

### Around line 73

68:         raise ValueError("y_min is outside motion limits")
69: 
70:     if not (limits.y_min <= profile.y_max <= limits.y_max):
71:         raise ValueError("y_max is outside motion limits")
72: 
73:     if not (limits.z_min <= profile.z <= limits.z_max):
74:         raise ValueError("z is outside motion limits")
75: 
76:     if profile.feedrate_xy <= 0:
77:         raise ValueError("feedrate_xy must be positive")
78: 
79:     if profile.feedrate_z <= 0:
80:         raise ValueError("feedrate_z must be positive")

## Prusa backend move_to and Z command generation

File: core\motion\prusa_gcode_backend.py


### Around line 31

26:         *,
27:         port: Optional[str] = None,
28:         baudrate: int = 115200,
29:         timeout: float = 0.5,
30:         auto_detect_port: bool = True,
31:         x_limits: Optional[Tuple[float, float]] = None,
32:         y_limits: Optional[Tuple[float, float]] = None,
33:         z_limits: Optional[Tuple[float, float]] = None,
34:     ):
35:         self.port = port
36:         self.baudrate = baudrate
37:         self.timeout = timeout
38:         self.auto_detect_port = auto_detect_port
39:         self.x_limits = x_limits

### Around line 32

27:         port: Optional[str] = None,
28:         baudrate: int = 115200,
29:         timeout: float = 0.5,
30:         auto_detect_port: bool = True,
31:         x_limits: Optional[Tuple[float, float]] = None,
32:         y_limits: Optional[Tuple[float, float]] = None,
33:         z_limits: Optional[Tuple[float, float]] = None,
34:     ):
35:         self.port = port
36:         self.baudrate = baudrate
37:         self.timeout = timeout
38:         self.auto_detect_port = auto_detect_port
39:         self.x_limits = x_limits
40:         self.y_limits = y_limits

### Around line 33

28:         baudrate: int = 115200,
29:         timeout: float = 0.5,
30:         auto_detect_port: bool = True,
31:         x_limits: Optional[Tuple[float, float]] = None,
32:         y_limits: Optional[Tuple[float, float]] = None,
33:         z_limits: Optional[Tuple[float, float]] = None,
34:     ):
35:         self.port = port
36:         self.baudrate = baudrate
37:         self.timeout = timeout
38:         self.auto_detect_port = auto_detect_port
39:         self.x_limits = x_limits
40:         self.y_limits = y_limits
41:         self.z_limits = z_limits

### Around line 39

34:     ):
35:         self.port = port
36:         self.baudrate = baudrate
37:         self.timeout = timeout
38:         self.auto_detect_port = auto_detect_port
39:         self.x_limits = x_limits
40:         self.y_limits = y_limits
41:         self.z_limits = z_limits
42:         self._ser = None
43:         self._connected = False
44:         self._last_position: Dict[str, float] = {}
45:         self._last_state: Dict = {"connected": False, "position": {}}
46: 
47:     # -------------------------

### Around line 40

35:         self.port = port
36:         self.baudrate = baudrate
37:         self.timeout = timeout
38:         self.auto_detect_port = auto_detect_port
39:         self.x_limits = x_limits
40:         self.y_limits = y_limits
41:         self.z_limits = z_limits
42:         self._ser = None
43:         self._connected = False
44:         self._last_position: Dict[str, float] = {}
45:         self._last_state: Dict = {"connected": False, "position": {}}
46: 
47:     # -------------------------
48:     # low-level helpers

### Around line 41

36:         self.baudrate = baudrate
37:         self.timeout = timeout
38:         self.auto_detect_port = auto_detect_port
39:         self.x_limits = x_limits
40:         self.y_limits = y_limits
41:         self.z_limits = z_limits
42:         self._ser = None
43:         self._connected = False
44:         self._last_position: Dict[str, float] = {}
45:         self._last_state: Dict = {"connected": False, "position": {}}
46: 
47:     # -------------------------
48:     # low-level helpers
49:     # -------------------------

### Around line 44

39:         self.x_limits = x_limits
40:         self.y_limits = y_limits
41:         self.z_limits = z_limits
42:         self._ser = None
43:         self._connected = False
44:         self._last_position: Dict[str, float] = {}
45:         self._last_state: Dict = {"connected": False, "position": {}}
46: 
47:     # -------------------------
48:     # low-level helpers
49:     # -------------------------
50:     def _require_serial(self) -> None:
51:         if serial is None:
52:             raise RuntimeError("pyserial is not installed. Run: python -m pip install pyserial")

### Around line 86

81:         return ports[0].device
82: 
83:     def _parse_m114(self, lines: List[str]) -> Dict[str, float]:
84:         """
85:         Parse M114 response lines into position dict.
86:         Expected tokens include X:.. Y:.. Z:.. (E optional).
87:         """
88:         joined = " ".join(lines)
89:         out: Dict[str, float] = {}
90:         for axis in ("X", "Y", "Z", "E"):
91:             m = re.search(rf"\b{axis}:\s*(-?\d+(?:\.\d+)?)", joined)
92:             if m:
93:                 out[axis.lower()] = float(m.group(1))
94:         return out

### Around line 90

85:         Parse M114 response lines into position dict.
86:         Expected tokens include X:.. Y:.. Z:.. (E optional).
87:         """
88:         joined = " ".join(lines)
89:         out: Dict[str, float] = {}
90:         for axis in ("X", "Y", "Z", "E"):
91:             m = re.search(rf"\b{axis}:\s*(-?\d+(?:\.\d+)?)", joined)
92:             if m:
93:                 out[axis.lower()] = float(m.group(1))
94:         return out
95: 
96:     def _check_limits(self, *, x: Optional[float], y: Optional[float], z: Optional[float]) -> None:
97:         checks = (
98:             ("X", x, self.x_limits),

### Around line 96

91:             m = re.search(rf"\b{axis}:\s*(-?\d+(?:\.\d+)?)", joined)
92:             if m:
93:                 out[axis.lower()] = float(m.group(1))
94:         return out
95: 
96:     def _check_limits(self, *, x: Optional[float], y: Optional[float], z: Optional[float]) -> None:
97:         checks = (
98:             ("X", x, self.x_limits),
99:             ("Y", y, self.y_limits),
100:             ("Z", z, self.z_limits),
101:         )
102:         for axis, value, limits in checks:
103:             if value is None or limits is None:
104:                 continue

### Around line 98

93:                 out[axis.lower()] = float(m.group(1))
94:         return out
95: 
96:     def _check_limits(self, *, x: Optional[float], y: Optional[float], z: Optional[float]) -> None:
97:         checks = (
98:             ("X", x, self.x_limits),
99:             ("Y", y, self.y_limits),
100:             ("Z", z, self.z_limits),
101:         )
102:         for axis, value, limits in checks:
103:             if value is None or limits is None:
104:                 continue
105:             low, high = limits
106:             if value < low or value > high:

### Around line 99

94:         return out
95: 
96:     def _check_limits(self, *, x: Optional[float], y: Optional[float], z: Optional[float]) -> None:
97:         checks = (
98:             ("X", x, self.x_limits),
99:             ("Y", y, self.y_limits),
100:             ("Z", z, self.z_limits),
101:         )
102:         for axis, value, limits in checks:
103:             if value is None or limits is None:
104:                 continue
105:             low, high = limits
106:             if value < low or value > high:
107:                 raise ValueError(f"{axis} target {value} is out of limits [{low}, {high}].")
