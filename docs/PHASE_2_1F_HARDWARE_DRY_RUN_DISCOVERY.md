# Phase 2.1F Hardware Dry-Run Discovery Report

Generated: 2026-06-17 11:01:25

## Safety

This discovery phase does not connect to serial hardware.
It does not send G-code.
It does not move the printer.

## Purpose

Find existing safe MK4S / Prusa / serial / dry-run modules so Phase 2.1 can connect the web GUI to proven project code instead of inventing a second hardware stack.

## Summary counts

- mk4s_prusa: 147 files
- serial: 156 files
- gcode_readonly: 103 files
- gcode_motion: 46 files
- dry_run_simulation: 178 files
- z_control: 223 files
- scan: 255 files
- web_api: 25 files

## mk4s_prusa

### `README.md`

- L3: Educational SPM prototype using a Prusa MK4S as a safe motion platform.
- L7: - Prusa MK4S connection works on COM5
- L44: - COM5 is the confirmed Prusa MK4S port.

### `ROADMAP_SPM_PRUSA.md`

- L1: # SPM / Prusa MK4S Project Roadmap
- L11: D:\SPM_Prusa_Project
- L14: All future development happens in D:\SPM_Prusa_Project.
- L19: The project uses the Prusa MK4S hardware as a scanning probe microscope style platform.
- L21: The realistic goal is micrometer-scale scanning, or the best possible resolution within the mechanical and sensor limits of the Prusa MK4S.
- L33: Platform: Prusa MK4S
- L44: Required: trace Z through GUI input, scan profile, validation, scan runner, MK4S command generation, and display.
- L49: Bug 3 - Real MK4S motion does not update the main scan window properly.
- L51: If motion is real but values are simulated, label it as: Real MK4S motion with simulated measurement values.
- L55: Goal: move active work from C:\SPM_Project to D:\SPM_Prusa_Project.
- L56: Completed: project copied to D:\SPM_Prusa_Project.
- L65: 3. Connect real MK4S scan loop to the live main scan window.

### `config\spm_hardware_initialized_profile.json`

- L6: "name": "Prusa MK4 controller",
- L12: "firmware_name": "Prusa-Firmware-Buddy 6.2.4+8909",
- L13: "machine_type": "Prusa-MK4",

### `config\spm_mk4s_config.json`

- L22: "description": "Educational SPM default using the original Prusa MK4S motion system and synthetic topography readback.",
- L37: "feedback": "MK4S Z height is used for clearance; fine SPM feedback is simulated until the later Z scanner is installed",
- L47: "xy_stage": "Original Prusa MK4S X/Y stage",
- L48: "z_stage": "Original Prusa MK4S Z axis",
- L53: "description": "Educational contact-probe preparation using original MK4S motion; real contact probe will be added later.",
- L68: "feedback": "contact threshold is planned later; current tests use original MK4S Z clearance plus dry-run feedback",
- L78: "xy_stage": "Prusa MK4S safe SPM area",
- L79: "z_stage": "Original Prusa MK4S Z axis now; fine Z scanner planned later",
- L84: "description": "AFM-style educational template using original MK4S motion; force feedback is simulated for now.",
- L109: "xy_stage": "Prusa MK4S safe SPM area",
- L110: "z_stage": "Original Prusa MK4S Z axis now; fine Z scanner planned later",
- L115: "description": "STM-style educational template using original MK4S motion; tunneling-current channel is simulated for now.",

### `core\ai\academic_ai_client.py`

- L1: """Academic AI advisory layer for the SPM Prusa project.
- L6: It must not directly execute MK4S motion commands.
- L53: "Confirm MK4S position readback before any Z move.",

### `core\ai\__init__.py`

- L1: """AI advisory modules for the SPM Prusa project."""

### `core\application\gui_scan_launcher.py`

- L53: from core.motion.prusa_gcode_backend import PrusaGcodeBackend
- L67: APP_TITLE = f"Educational SPM {APP_VERSION} - Operator Workspace - Prusa MK4S"
- L300: self.stage_position_label = QLabel("Current MK4S position: X unknown | Y unknown | Z unknown")
- L320: self.query_position_btn = QPushButton("READ MK4S POSITION")
- L322: self.park_btn = QPushButton("PARK MK4S")
- L492: # MK4S Z / Height Control panel
- L496: z_group = QGroupBox("3 MK4S Z Height / Approach Training")
- L499: z_height_group = QGroupBox("MK4S Z Height / Safe Position")
- L831: "Current hardware target: Original Prusa MK4S motion platform.\n"
- L934: "- Installed motion hardware: original Prusa MK4S X/Y/Z system.\n"
- L938: "1. Prepare the MK4S, object, and workspace. Make sure the bed and tool path are clear.\n"
- L939: "2. Press **INITIATE SYSTEM CHECK** to validate settings and query MK4S communication without motion.\n"

### `core\application\hardware_test_console_gui.py`

- L321: self.smart_recommendation.setText("Recommendation: check MK4S power, USB, COM5, and close other serial tools.")
- L442: "4. Confirm the popup while watching the MK4S."
- L452: "Continue only if the MK4S path is clear and you are watching the hardware."

### `core\application\hardware_test_control_cli.py`

- L1: """CLI for supervised MK4S hardware test controls.

### `core\application\workstation_status.py`

- L83: f"Machine: Prusa MK4S on {self.machine_port} @ {self.machine_baudrate}; "

### `core\education\config_loader.py`

- L9: """Load SPM MK4S JSON configuration."""
- L15: def get_prusa_backend_kwargs(config):
- L16: """Extract PrusaGcodeBackend keyword arguments from config."""

### `core\motion\motion_backend.py`

- L12: - G-code driven systems (e.g. Prusa MK4S)

### `core\motion\parking.py`

- L3: from core.education.config_loader import get_parking_position, get_prusa_backend_kwargs
- L4: from core.motion.prusa_gcode_backend import PrusaGcodeBackend
- L8: """Park MK4S by retracting Z first, then moving XY to the parking corner."""
- L11: backend = PrusaGcodeBackend(**get_prusa_backend_kwargs(config))

### `core\motion\prusa_gcode_backend.py`

- L15: class PrusaGcodeBackend(MotionBackend):
- L17: Motion backend using a Prusa MK4S (or compatible) printer controlled via G-code.
- L54: def _auto_detect_prusa_port(self) -> Optional[str]:
- L56: Best-effort serial port discovery for Prusa/USB CDC devices.
- L69: # Prefer ports that look like Prusa USB serial endpoints.
- L72: if "prusa" in blob:
- L151: self.port = self._auto_detect_prusa_port()
- L154: "PrusaGcodeBackend.port is not set and auto-detection failed "

### `core\system\hardware_diagnostics.py`

- L5: from core.motion.prusa_gcode_backend import PrusaGcodeBackend
- L77: def check_prusa_communication(config: dict) -> HardwareCheck:
- L81: backend = PrusaGcodeBackend(
- L95: name="Prusa MK4S XY motion controller",
- L110: name="Prusa MK4S XY motion controller",
- L121: message="Fine Z scanner communication is not part of the current MK4S-original hardware test.",
- L123: "Current hardware test uses the original Prusa MK4S X/Y/Z motion system.",
- L147: message="Original MK4S machine limits and recommended SPM-safe limits loaded from configuration.",
- L156: check_prusa_communication(config),

### `core\system\hardware_profile.py`

- L19: return f"MK4S soft {self.firmware_min:g}..{self.firmware_max:g} {self.unit}"
- L31: manual_source: str = "Prusa MK4S handbook v1.01, Product Information"
- L43: "Higher resolution means more MK4S moves. Start 5 x 5, then 9 x 9, "
- L47: "Machine limits now follow the original MK4S build volume. "
- L66: f"Official MK4S build volume: {self.official_build_volume}\n"
- L85: f"Official MK4S build volume {self.official_build_volume}; "

### `core\system\hardware_test_controls.py`

- L1: """Supervised hardware test controls for the MK4S scanner layer.
- L14: from core.motion.prusa_gcode_backend import PrusaGcodeBackend
- L169: backend = PrusaGcodeBackend(

### `core\system\mk4s_z_auto_approach.py`

- L1: """Focused MK4S Z auto-approach sequence for the Educational SPM project."""
- L134: message="Preview only. No MK4S movement was sent.",
- L144: log.write(f"\n=== MK4S Z AUTO APPROACH {time.strftime('%Y-%m-%d %H:%M:%S')} ===\n")
- L161: message=f"MK4S Z auto approach completed. Final Z={final_z:.2f}. Raw log: {raw_path}",
- L192: message="Preview only. No MK4S movement was sent.",
- L237: message="Preview only. No MK4S movement was sent.",

### `core\system\smart_hardware_assessment.py`

- L88: recommendation = "Connection looks healthy. Next: run one supervised 1-5 mm test step while watching the MK4S."
- L94: recommendation = "Do not move hardware yet. Check USB, power, COM5, and MK4S status, then run Smart System Check again."

### `core\system\workstation_initializer.py`

- L33: This performs real read-only MK4S communication checks and prepares the

### `core\web\operator_console_server.py`

- L1: """Local web operator console server for the Prusa MK4S SPM project."""
- L26: "purpose": "Browser-based SPM Prusa operator console foundation.",
- L111: "project": "SPM Prusa MK4S",
- L183: print(f"SPM Prusa web operator console running at http://{host}:{port}")
- L189: parser = argparse.ArgumentParser(description="Run the local SPM Prusa web operator console.")

### `core\web\__init__.py`

- L1: """Web-facing local services for the SPM Prusa project."""

### `data\phase9_6_dryrun_probe.metadata.json`

- L12: "name": "Prusa MK4 controller",
- L18: "firmware_name": "Prusa-Firmware-Buddy 6.2.4+8909",
- L19: "machine_type": "Prusa-MK4",

### `docs\GITHUB_COMPARISON_REPORT_2026-06-09.txt`

- L16: > ca161c0 feat: wire Connect toggle to Prusa backend and add hardware/dry-run flags
- L17: > 817e66a test: add Prusa connect failure test for missing port
- L18: > 45323dc feat: add Prusa G-code serial backend and safe ping tool
- L27: > 2d0bf7e core: add soft connect flag for PrusaGcodeBackend
- L28: > f9197db core: add PrusaGcodeBackend stub
- L30: > 45f8dac docs: add project overview and Prusa MK4S decision
- L75: core/motion/prusa_gcode_backend.py                 | 137 +------
- L106: docs/MK4S_BRINGUP_CHECKLIST.md                     |  53 ---
- L107: docs/MK4S_BRINGUP_LOG_2026-06-09.md                | 174 ---------
- L113: ...-prusa-mk4s-kit-assembly_2167_en_2025-09-26.pdf | Bin 33614421 -> 0 bytes
- L114: docs/prusa3d_manual_mk4s_mk39s_101_en.pdf          | Bin 44157299 -> 0 bytes
- L229: tests/motion/test_prusa_backend.py                 |  40 --

### `docs\MK4S_BRINGUP_CHECKLIST.md`

- L1: ## MK4S Bring-Up Checklist for SPM
- L12: - Connect MK4S via USB to control host

### `docs\MK4S_BRINGUP_LOG_2026-06-09.md`

- L1: # SPM MK4S Bring-Up Log
- L5: Printer: Prusa MK4S / MK4-compatible firmware
- L7: Firmware: Prusa-Firmware-Buddy 6.2.4
- L13: - Prusa serial connection works on COM5
- L145: - Prusa MK4S connected on COM5

### `docs\MK4S_MACHINE_LIMITS_AND_HARDWARE_TEST_2026-06-11.md`

- L1: # MK4S Machine Limits and Hardware Test - 2026-06-11
- L20: - Firmware: Prusa-Firmware-Buddy 6.2.4+8909
- L21: - Machine type reported: Prusa-MK4
- L34: These are the MK4S firmware soft limits, not the SPM operating envelope.
- L93: - No-motion MK4S limits/current-position query: PASS
- L135: - Move each MK4S axis one by one to the current SPM-safe minimum and maximum.
- L141: - This test did not move to full MK4S firmware soft-endstop extremes.
- L182: ## 2026-06-11 Official MK4S Maximum Position Test
- L186: - Official Prusa MK4S product page reports build volume: 250 x 210 x 220 mm.
- L187: - Official Prusa MK4S/MK3.9S handbook v1.01, Product Information page, reports build volume: 250 x 210 x 220 mm.
- L191: - Test the official maximum positions from the Prusa build volume.
- L231: ## 2026-06-11 Official MK4S X/Y Minimum Position Test

### `docs\PHASE1_CODE_MAP.md`

- L3: Project: D:\SPM_Prusa_Project
- L100: - docs\PHASE1_CODE_MAP.md:98: - docs\PHASE1_CODE_MAP.md:67: - docs\PHASE1_CODE_MAP.md:7: This report maps where Z setpoint, preview, half-ball/generated surface, scan runner, MK4S 
- L102: - docs\PHASE1_CODE_MAP.md:100: - docs\PHASE1_CODE_MAP.md:219: - docs\PHASE1_CODE_MAP.md:7: This report maps where Z setpoint, preview, half-ball/generated surface, scan runner, MK4
- L103: - docs\PHASE1_CODE_MAP.md:101: - docs\PHASE1_CODE_MAP.md:223: - docs\PHASE1_CODE_MAP.md:7: This report maps where Z setpoint, preview, half-ball/generated surface, scan runner, MK4
- L105: - docs\PHASE1_CODE_MAP.md:316: - docs\PHASE1_CODE_MAP.md:67: - docs\PHASE1_CODE_MAP.md:7: This report maps where Z setpoint, preview, half-ball/generated surface, scan runner, MK4S
- L106: - docs\PHASE1_CODE_MAP.md:318: - docs\PHASE1_CODE_MAP.md:219: - docs\PHASE1_CODE_MAP.md:7: This report maps where Z setpoint, preview, half-ball/generated surface, scan runner, MK4
- L107: - docs\PHASE1_CODE_MAP.md:319: - docs\PHASE1_CODE_MAP.md:223: - docs\PHASE1_CODE_MAP.md:7: This report maps where Z setpoint, preview, half-ball/generated surface, scan runner, MK4
- L108: - docs\PHASE1_CODE_MAP.md:323: - docs\PHASE1_CODE_MAP.md:67: - docs\PHASE1_CODE_MAP.md:7: This report maps where Z setpoint, preview, half-ball/generated surface, scan runner, MK4S
- L109: - docs\PHASE1_CODE_MAP.md:324: - docs\PHASE1_CODE_MAP.md:219: - docs\PHASE1_CODE_MAP.md:7: This report maps where Z setpoint, preview, half-ball/generated surface, scan runner, MK4
- L110: - docs\PHASE1_CODE_MAP.md:326: - docs\PHASE1_CODE_MAP.md:223: - docs\PHASE1_CODE_MAP.md:7: This report maps where Z setpoint, preview, half-ball/generated surface, scan runner, MK4
- L335: - core\system\mk4s_z_auto_approach.py:119: message="Preview only. No MK4S movement was sent.",
- L337: - core\system\mk4s_z_auto_approach.py:177: message="Preview only. No MK4S movement was sent.",

### `docs\PHASE1_CODE_ONLY_MAP.md`

- L3: Project: D:\SPM_Prusa_Project
- L46: - core\motion\prusa_gcode_backend.py:21: - movement happens only via move_to()/home().
- L47: - core\motion\prusa_gcode_backend.py:214: def move_to(
- L48: - core\motion\prusa_gcode_backend.py:224: raise ValueError("move_to requires at least one axis target (x, y, or z).")
- L49: - core\motion\prusa_gcode_backend.py:226: self._check_limits(x=x, y=y, z=z)
- L65: - core\system\mk4s_z_auto_approach.py:146: message=f"MK4S Z auto approach completed. Final Z={final_z:.2f}. Raw log: {raw_path}",
- L215: - core\application\gui_scan_launcher.py:2569: "Current step: real motion is enabled. Supervise the MK4S and run hardware scan only with a clear object/surface path."
- L337: - core\motion\prusa_gcode_backend.py:75: # Fallbacks that work on Linux/macOS/Windows for USB serial printers.
- L338: - core\motion\prusa_gcode_backend.py:186: self._last_position.update(parsed)
- L339: - core\motion\prusa_gcode_backend.py:209: self._last_position.update(parsed)
- L340: - core\motion\prusa_gcode_backend.py:255: self._last_position.update(parsed)
- L358: - tests\motion\test_prusa_backend.py:31: def test_move_to_updates_cached_position(monkeypatch):

### `docs\PHASE1_Z_CLIPBOARD_REPORT.txt`

- L2: Project: D:\SPM_Prusa_Project
- L103: 53: from core.motion.prusa_gcode_backend import PrusaGcodeBackend
- L124: 53: from core.motion.prusa_gcode_backend import PrusaGcodeBackend
- L146: 53: from core.motion.prusa_gcode_backend import PrusaGcodeBackend
- L170: 53: from core.motion.prusa_gcode_backend import PrusaGcodeBackend
- L245: 53: from core.motion.prusa_gcode_backend import PrusaGcodeBackend
- L259: 67: APP_TITLE = f"Educational SPM {APP_VERSION} - Operator Workspace - Prusa MK4S"
- L269: 53: from core.motion.prusa_gcode_backend import PrusaGcodeBackend
- L283: 67: APP_TITLE = f"Educational SPM {APP_VERSION} - Operator Workspace - Prusa MK4S"
- L598: FILE: core\motion\prusa_gcode_backend.py
- L620: 54:     def _auto_detect_prusa_port(self) -> Optional[str]:
- L622: 56:         Best-effort serial port discovery for Prusa/USB CDC devices.

## serial

### `README.md`

- L7: - Prusa MK4S connection works on COM5
- L44: - COM5 is the confirmed Prusa MK4S port.
- L45: - COM4 is a phantom FTDI device and should be ignored.

### `requirements.txt`

- L5: pyserial

### `config\spm_hardware_initialized_profile.json`

- L7: "port": "COM5",
- L8: "baudrate": 115200,
- L9: "usb_name": "Serielles USB-Ger\u00e4t (COM5)",

### `config\spm_mk4s_config.json`

- L3: "port": "COM5",
- L4: "baudrate": 115200

### `core\application\gui_scan_launcher.py`

- L549: # Placeholder: COM port, baudrate, machine connection, hardware readiness, last known state.
- L967: f"Controller: Prusa MK4S on {self.config['printer']['port']} @ {self.config['printer']['baudrate']}\n"
- L1315: baudrate=int(printer["baudrate"]),
- L1415: self.hardware_status_label.setText("Hardware / System Connection: POWERED OFF / SAFE PARK COMPLETE")

### `core\application\hardware_information_cli.py`

- L3: Default mode is dry-run planning. Use --real to open the confirmed serial port
- L26: parser.add_argument("--real", action="store_true", help="Open serial port and run read-only hardware command.")
- L27: parser.add_argument("--port", default=None, help="Override configured serial port.")
- L28: parser.add_argument("--baudrate", type=int, default=None, help="Override configured baudrate.")
- L37: print("DRY RUN ONLY. No serial port opened and no hardware command sent.")
- L42: results = run_real_information_exchange(args.action, port=args.port, baudrate=args.baudrate)

### `core\application\hardware_startup_cli.py`

- L12: print(f"baudrate={result.baudrate}")

### `core\application\hardware_test_console_gui.py`

- L149: self.real_readonly_checkbox = QCheckBox("Run real read-only exchange on COM5")
- L309: self.smart_state.setText("State: checking COM5...")
- L321: self.smart_recommendation.setText("Recommendation: check MK4S power, USB, COM5, and close other serial tools.")

### `core\application\workstation_status.py`

- L9: machine_baudrate: int
- L29: machine_baudrate=int(printer["baudrate"]),
- L83: f"Machine: Prusa MK4S on {self.machine_port} @ {self.machine_baudrate}; "

### `core\education\config_loader.py`

- L22: "baudrate": printer["baudrate"],

### `core\hardware\hardware_command_bus.py`

- L50: response = f"ERROR: UNKNOWN COMMAND {command_clean}"

### `core\motion\prusa_gcode_backend.py`

- L10: import serial  # type: ignore
- L12: serial = None
- L20: - connect() only opens serial + sets absolute mode (G90). No movement.
- L28: baudrate: int = 115200,
- L36: self.baudrate = baudrate
- L50: def _require_serial(self) -> None:
- L51: if serial is None:
- L52: raise RuntimeError("pyserial is not installed. Run: python -m pip install pyserial")
- L56: Best-effort serial port discovery for Prusa/USB CDC devices.
- L58: if serial is None:
- L61: from serial.tools import list_ports  # type: ignore
- L69: # Prefer ports that look like Prusa USB serial endpoints.

### `core\system\hardware_diagnostics.py`

- L41: def list_serial_ports() -> list[str]:
- L43: from serial.tools import list_ports  # type: ignore
- L53: def check_serial_inventory(ignored_ports: tuple[str, ...] = ("COM4",)) -> HardwareCheck:
- L54: ports = list_serial_ports()
- L59: message="No serial ports detected by pyserial.",
- L72: message=f"{len(active)} active serial candidate(s), {len(ignored)} ignored.",
- L80: baudrate = int(printer["baudrate"])
- L83: baudrate=baudrate,
- L104: f"Baudrate: {baudrate}",
- L154: check_serial_inventory(),

### `core\system\hardware_information_exchange.py`

- L14: import serial
- L79: baudrate: int | None = None,
- L85: selected_baudrate = int(baudrate or settings["baudrate"])
- L91: with serial.Serial(selected_port, selected_baudrate, timeout=timeout) as ser:

### `core\system\hardware_startup_initializer.py`

- L5: - Opens confirmed serial port
- L18: import serial
- L23: READONLY_STARTUP_COMMANDS = ("M115", "M105", "M119")
- L37: baudrate: int
- L44: baudrate: int | None = None,
- L50: selected_baudrate = baudrate or int(settings["baudrate"])
- L54: with serial.Serial(selected_port, selected_baudrate, timeout=timeout) as ser:
- L57: for command in READONLY_STARTUP_COMMANDS:
- L82: baudrate=selected_baudrate,

### `core\system\hardware_test_controls.py`

- L171: baudrate=int(settings["baudrate"]),

### `core\system\mk4s_z_auto_approach.py`

- L9: import serial
- L100: def _read_until_ok(ser: serial.Serial, *, timeout_s: float) -> list[str]:
- L141: with serial.Serial(settings["port"], int(settings["baudrate"]), timeout=2) as ser:
- L200: with serial.Serial(settings["port"], int(settings["baudrate"]), timeout=2) as ser:
- L242: with serial.Serial(settings["port"], int(settings["baudrate"]), timeout=2) as ser:

### `core\system\smart_hardware_assessment.py`

- L94: recommendation = "Do not move hardware yet. Check USB, power, COM5, and MK4S status, then run Smart System Check again."

### `core\z_control\z_driver_arduino.py`

- L4: def __init__(self, port="COM3", baudrate=115200):
- L5: import serial
- L7: self.serial = serial.Serial(port, baudrate, timeout=1)
- L8: except serial.SerialException as e:
- L9: raise RuntimeError(f"Unable to open serial port: {e}")
- L13: self.serial.write(f"MOVE {z_position}\n".encode())
- L17: self.serial.write(b"GET_POS\n")
- L18: response = self.serial.readline().decode().strip()
- L25: self.serial.close()

### `core\z_control\z_driver_arduino_safe.py`

- L13: In dry-run mode, no real serial connection is opened and no hardware moves.
- L16: def __init__(self, port: str = "COM5", baudrate: int = 115200, dry_run: bool = True):
- L18: self.baudrate = baudrate
- L20: self.serial_conn = None
- L40: self.serial_conn = None
- L120: "baudrate": self.baudrate,
- L124: "serial_open": self.serial_conn is not None,

### `data\phase9_6_dryrun_probe.metadata.json`

- L13: "port": "COM5",
- L14: "baudrate": 115200,
- L15: "usb_name": "Serielles USB-Ger\u00e4t (COM5)",

### `docs\ACADEMIC_AI_API_INTEGRATION_PLAN_2026-06-12.md`

- L38: - Raw serial log.

### `docs\CURRENT_PROJECT_STATUS_2026-06-09.md`

- L40: - serial port selector
- L55: [DRY RUN] Connecting to Arduino on COM5

### `docs\GITHUB_COMPARISON_REPORT_2026-06-09.txt`

- L2: ?? GITHUB_COMPARISON_REPORT.txt
- L5: === LOCAL COMMIT ===
- L8: === GITHUB COMMIT ===
- L11: === COMMIT RELATION: main...origin/main ===
- L14: > 1fe12b3 ux: add serial port dropdown with refresh and safe connect handling
- L18: > 45323dc feat: add Prusa G-code serial backend and safe ping tool

### `docs\MK4S_BRINGUP_CHECKLIST.md`

- L13: - Identify serial port:
- L15: - Confirm user has serial permissions (`dialout` group)

### `docs\MK4S_BRINGUP_LOG_2026-06-09.md`

- L6: Serial port: COM5
- L13: - Prusa serial connection works on COM5
- L47: - COM4 is an old FTDI phantom device and should be ignored
- L86: - Refactored tools\safe_raster_3x3_test.py to read COM port, limits, and feedrates from config\spm_mk4s_config.json
- L145: - Prusa MK4S connected on COM5

### `docs\MK4S_MACHINE_LIMITS_AND_HARDWARE_TEST_2026-06-11.md`

- L19: - Port: COM5

### `docs\PHASE1_CODE_MAP.md`

- L1039: - core\motion\prusa_gcode_backend.py:75: # Fallbacks that work on Linux/macOS/Windows for USB serial printers.
- L1102: - core\application\gui_scan_launcher.py:957: f"Controller: Prusa MK4S on {self.config['printer']['port']} @ {self.config['printer']['baudrate']}\n"
- L1135: - core\application\hardware_test_console_gui.py:321: self.smart_recommendation.setText("Recommendation: check MK4S power, USB, COM5, and close other serial tools.")
- L1139: - core\application\workstation_status.py:83: f"Machine: Prusa MK4S on {self.machine_port} @ {self.machine_baudrate}; "
- L1173: - core\application\gui_scan_launcher.py:957: f"Controller: Prusa MK4S on {self.config['printer']['port']} @ {self.config['printer']['baudrate']}\n"
- L1177: - core\application\workstation_status.py:83: f"Machine: Prusa MK4S on {self.machine_port} @ {self.machine_baudrate}; "
- L1187: - core\motion\prusa_gcode_backend.py:56: Best-effort serial port discovery for Prusa/USB CDC devices.
- L1188: - core\motion\prusa_gcode_backend.py:69: # Prefer ports that look like Prusa USB serial endpoints.
- L1205: - tools\phase9_xy_10x10_topography_skeleton.py:341: executor = RobustPrusaExecutor(settings["port"], int(settings["baudrate"]), raw_logger)
- L1230: - tools\run_safe_software_check.ps1:13: .\.venv\Scripts\python.exe tools\prusa_ping.py --port COM5 --no-auto-detect
- L1241: - tests\motion\test_prusa_connect.py:7: b = PrusaGcodeBackend(port="COM_DOES_NOT_EXIST_9999")

### `docs\PHASE1_CODE_ONLY_MAP.md`

- L337: - core\motion\prusa_gcode_backend.py:75: # Fallbacks that work on Linux/macOS/Windows for USB serial printers.
- L396: - core\application\gui_scan_launcher.py:957: f"Controller: Prusa MK4S on {self.config['printer']['port']} @ {self.config['printer']['baudrate']}\n"
- L431: - core\application\hardware_information_cli.py:3: Default mode is dry-run planning. Use --real to open the confirmed serial port
- L432: - core\application\hardware_information_cli.py:26: parser.add_argument("--real", action="store_true", help="Open serial port and run read-only hardware command.")
- L433: - core\application\hardware_information_cli.py:27: parser.add_argument("--port", default=None, help="Override configured serial port.")
- L434: - core\application\hardware_information_cli.py:37: print("DRY RUN ONLY. No serial port opened and no hardware command sent.")
- L436: - core\application\hardware_test_console_gui.py:321: self.smart_recommendation.setText("Recommendation: check MK4S power, USB, COM5, and close other serial tools.")
- L440: - core\application\workstation_status.py:83: f"Machine: Prusa MK4S on {self.machine_port} @ {self.machine_baudrate}; "
- L451: - core\motion\prusa_gcode_backend.py:10: import serial  # type: ignore
- L452: - core\motion\prusa_gcode_backend.py:12: serial = None
- L455: - core\motion\prusa_gcode_backend.py:20: - connect() only opens serial + sets absolute mode (G90). No movement.
- L456: - core\motion\prusa_gcode_backend.py:50: def _require_serial(self) -> None:

### `docs\PHASE1_Z_CLIPBOARD_REPORT.txt`

- L602: 36:         self.baudrate = baudrate
- L616: 50:     def _require_serial(self) -> None:
- L617: 51:         if serial is None:
- L618: 52:             raise RuntimeError("pyserial is not installed. Run: python -m pip install pyserial")
- L622: 56:         Best-effort serial port discovery for Prusa/USB CDC devices.
- L624: 58:         if serial is None:
- L659: 170:             "baudrate": self.baudrate,
- L845: 85: def _read_until_ok(ser: serial.Serial, *, timeout_s: float) -> list[str]:
- L893: 185:     with serial.Serial(settings["port"], int(settings["baudrate"]), timeout=2) as ser:

## gcode_readonly

### `config\spm_hardware_initialized_profile.json`

- L18: "M115",
- L19: "M105",
- L20: "M119"
- L23: "M115": "ok; firmware and machine identity confirmed",
- L24: "M105": "ok; temperature/status readable",
- L25: "M119": "ok; endstop status readable"

### `core\application\gui_scan_launcher.py`

- L1126: if not detail.startswith("M114:"):

### `core\application\hardware_test_console_gui.py`

- L150: self.real_readonly_checkbox.setToolTip("Sends only M115/M105/M119/M114. No motion commands.")

### `core\motion\prusa_gcode_backend.py`

- L85: Parse M114 response lines into position dict.
- L183: lines = self.send_gcode("M114", timeout=2.5)
- L206: lines = self.send_gcode("M114", timeout=3.0)
- L252: lines = self.send_gcode("M114", timeout=2.5)

### `core\system\hardware_diagnostics.py`

- L90: firmware_lines = backend.send_gcode("M115", timeout=4.0)
- L91: position_lines = backend.send_gcode("M114", timeout=4.0)
- L105: f"M115: {' | '.join(firmware_lines) if firmware_lines else 'no response text'}",
- L106: f"M114: {' | '.join(position_lines) if position_lines else 'no response text'}",

### `core\system\hardware_information_exchange.py`

- L20: "IDENTITY": "M115",
- L21: "TEMPERATURE": "M105",
- L22: "ENDSTOPS": "M119",
- L23: "POSITION": "M114",

### `core\system\hardware_startup_initializer.py`

- L23: READONLY_STARTUP_COMMANDS = ("M115", "M105", "M119")

### `core\system\hardware_test_controls.py`

- L83: return HardwareTestPlan(action_clean, ["M114"], False, "Read-only XYZ position query.")
- L88: [f"G1 Z{SAFE_RETRACT_Z:.2f} F{DEFAULT_Z_FEEDRATE:.0f}", "M400", "M114"],
- L101: "M114",
- L120: [f"G1 {axis.upper()}{target:.2f} F{feedrate:.0f}", "M400", "M114"],

### `core\system\mk4s_z_auto_approach.py`

- L59: "M114",
- L66: "M114",
- L94: commands.extend([f"G1 Z{z_value:.2f} F{feedrate:.0f}", "M400", "M114"])
- L96: commands.extend([f"G1 Z{safe_retract_z:.2f} F600", "M400", "M114"])
- L202: ser.write(b"M114\n")
- L213: for gcode in ("G90", command, "M400", "M114"):
- L244: for gcode in ("G90", command, "M400", "M114"):

### `core\web\system_control.py`

- L33: "M115 ; firmware/version read-only check",
- L34: "M119 ; endstop/probe state read-only check",
- L35: "M105 ; temperature read-only check",
- L36: "M114 ; position read-only check",

### `docs\MK4S_BRINGUP_LOG_2026-06-09.md`

- L14: - M115 firmware query works
- L15: - M114 position readback works

### `docs\MK4S_MACHINE_LIMITS_AND_HARDWARE_TEST_2026-06-11.md`

- L11: - `M115` firmware info
- L12: - `M114` current position
- L13: - `M119` endstop status

### `docs\PHASE1_CODE_MAP.md`

- L1250: ## Pattern: M114
- L1252: - core\application\gui_scan_launcher.py:1111: if not detail.startswith("M114:"):
- L1253: - core\application\hardware_test_console_gui.py:150: self.real_readonly_checkbox.setToolTip("Sends only M115/M105/M119/M114. No motion commands.")
- L1255: - core\motion\prusa_gcode_backend.py:85: Parse M114 response lines into position dict.
- L1256: - core\motion\prusa_gcode_backend.py:183: lines = self.send_gcode("M114", timeout=2.5)
- L1258: - core\motion\prusa_gcode_backend.py:206: lines = self.send_gcode("M114", timeout=3.0)
- L1260: - core\motion\prusa_gcode_backend.py:252: lines = self.send_gcode("M114", timeout=2.5)
- L1262: - core\system\hardware_diagnostics.py:91: position_lines = backend.send_gcode("M114", timeout=4.0)
- L1263: - core\system\hardware_diagnostics.py:106: f"M114: {' | '.join(position_lines) if position_lines else 'no response text'}",
- L1264: - core\system\hardware_information_exchange.py:23: "POSITION": "M114",
- L1265: - core\system\hardware_test_controls.py:83: return HardwareTestPlan(action_clean, ["M114"], False, "Read-only XYZ position query.")
- L1266: - core\system\hardware_test_controls.py:88: [f"G1 Z{SAFE_RETRACT_Z:.2f} F{DEFAULT_Z_FEEDRATE:.0f}", "M400", "M114"],

### `docs\PHASE1_CODE_ONLY_MAP.md`

- L51: - core\system\hardware_test_controls.py:88: [f"G1 Z{SAFE_RETRACT_Z:.2f} F{DEFAULT_Z_FEEDRATE:.0f}", "M400", "M114"],
- L60: - core\system\mk4s_z_auto_approach.py:79: commands.extend([f"G1 Z{z_value:.2f} F{feedrate:.0f}", "M400", "M114"])
- L61: - core\system\mk4s_z_auto_approach.py:81: commands.extend([f"G1 Z{safe_retract_z:.2f} F600", "M400", "M114"])
- L400: - core\application\gui_scan_launcher.py:1111: if not detail.startswith("M114:"):
- L435: - core\application\hardware_test_console_gui.py:150: self.real_readonly_checkbox.setToolTip("Sends only M115/M105/M119/M114. No motion commands.")
- L467: - core\motion\prusa_gcode_backend.py:85: Parse M114 response lines into position dict.
- L473: - core\motion\prusa_gcode_backend.py:183: lines = self.send_gcode("M114", timeout=2.5)
- L475: - core\motion\prusa_gcode_backend.py:206: lines = self.send_gcode("M114", timeout=3.0)
- L478: - core\motion\prusa_gcode_backend.py:252: lines = self.send_gcode("M114", timeout=2.5)
- L491: - core\system\hardware_diagnostics.py:91: position_lines = backend.send_gcode("M114", timeout=4.0)
- L493: - core\system\hardware_diagnostics.py:106: f"M114: {' | '.join(position_lines) if position_lines else 'no response text'}",

### `docs\PHASE1_Z_CLIPBOARD_REPORT.txt`

- L672: 183:             lines = self.send_gcode("M114", timeout=2.5)
- L682: 183:             lines = self.send_gcode("M114", timeout=2.5)
- L703: 183:             lines = self.send_gcode("M114", timeout=2.5)
- L741: 206:             lines = self.send_gcode("M114", timeout=3.0)
- L769: 59:         "M114",
- L776: 66:         "M114",
- L789: 66:         "M114",
- L802: 79:         commands.extend([f"G1 Z{z_value:.2f} F{feedrate:.0f}", "M400", "M114"])
- L804: 81:         commands.extend([f"G1 Z{safe_retract_z:.2f} F600", "M400", "M114"])
- L813: 66:         "M114",
- L826: 79:         commands.extend([f"G1 Z{z_value:.2f} F{feedrate:.0f}", "M400", "M114"])
- L828: 81:         commands.extend([f"G1 Z{safe_retract_z:.2f} F600", "M400", "M114"])

### `docs\PHASE1_Z_GUI_FUNCTIONS.md`

- L1060: 183:             lines = self.send_gcode("M114", timeout=2.5)
- L1105: 206:             lines = self.send_gcode("M114", timeout=3.0)
- L1114: 206:             lines = self.send_gcode("M114", timeout=3.0)
- L1280: - `core\system\hardware_test_controls.py`:88: [f"G1 Z{SAFE_RETRACT_Z:.2f} F{DEFAULT_Z_FEEDRATE:.0f}", "M400", "M114"],

### `docs\PHASE1_Z_INVESTIGATION_SMALL.md`

- L676: 85:         Parse M114 response lines into position dict.
- L689: 85:         Parse M114 response lines into position dict.

### `docs\PHASE_2_1E_MAIN_SYSTEM_DRY_RUN.md`

- L34: - `M115`
- L35: - `M119`
- L36: - `M105`
- L37: - `M114`

### `docs\PHASE_7_REPAIR_STATUS_2026-06-10.md`

- L128: - Firmware query `M115`: PASS, Prusa-Firmware-Buddy 6.2.4+8909
- L129: - Position query `M114`: PASS, X54 Y54 Z20

### `docs\PHASE_9_6_ROBUST_EXECUTOR_ROADMAP_2026-06-12.md`

- L20: and delayed `ok` / `M114` responses during longer motion queues. The old script reset the input buffer before every command and only saved data after the whole scan, so failures co
- L70: - `M115`
- L71: - `M105`
- L72: - `M119`
- L73: - `M114`
- L163: - Temperature/status readback succeeded with `M105`.
- L164: - Endstop readback succeeded with `M119`; all min/max endstops reported open.
- L165: - Position readback succeeded with `M114`: `X=125.00`, `Y=105.00`, `Z=120.00`.

### `docs\SPM_PC_HANDOFF.md`

- L56: - M115 firmware query works
- L57: - M114 position query works
- L128: - M115 firmware query
- L129: - M114 position query

### `docs\SPM_PROFESSIONAL_PHASE_ROADMAP.md`

- L462: - M115
- L463: - M105
- L464: - M119

### `docs\TWO_LAYER_SPM_DEVELOPMENT_ROADMAP_2026-06-12.md`

- L28: - `IDENTITY -> M115`
- L29: - `TEMPERATURE -> M105`
- L30: - `ENDSTOPS -> M119`
- L31: - `POSITION -> M114`
- L183: - `M115`: Prusa MK4 firmware identity confirmed.
- L184: - `M105`: temperature/status readback succeeded.
- L185: - `M119`: all endstops reported open.
- L186: - `M114`: position readback succeeded at `X=125.00`, `Y=105.00`, `Z=120.00`.
- L256: - `READ_POSITION` is an `M114` status command and should be easy to run as a real safe check without unlocking motion.
- L267: - `READ_POSITION` executed from the real execute button now runs the read-only `M114` path, not the supervised motion path.

### `docs\versions\v0.10.0_matrix_workspace_phase1_2026-06-11\backup\gui_scan_launcher.py`

- L998: if not detail.startswith("M114:"):

### `docs\versions\v0.10.1_clear_workstation_windows_2026-06-11\backup\gui_scan_launcher.py`

- L991: if not detail.startswith("M114:"):

### `docs\versions\v0.11.0_live_spm_raster_measurement_2026-06-11\backup\gui_scan_launcher.py`

- L1038: if not detail.startswith("M114:"):

### `docs\versions\v0.11.1_crash_hardened_live_measurement_2026-06-11\backup\gui_scan_launcher.py`

- L1038: if not detail.startswith("M114:"):

### `docs\versions\v0.11.2_text_live_scan_stability_2026-06-11\backup\gui_scan_launcher.py`

- L1046: if not detail.startswith("M114:"):

### `docs\versions\v0.13.0_phase7_general_system_initialization_2026-06-11\README.md`

- L9: - Verified real hardware startup using M115, M105, M119

### `docs\versions\v0.13.0_phase7_general_system_initialization_2026-06-11\backup\hardware_startup_initializer.py`

- L23: READONLY_STARTUP_COMMANDS = ("M115", "M105", "M119")

## gcode_motion

### `config\spm_hardware_initialized_profile.json`

- L57: "tested_command": "G1 X251 followed by G1 X1",
- L64: "tested_command": "G1 Y211 followed by G1 Y1",
- L70: "tested_command": "G1 Z120 followed by G1 Z100",

### `core\motion\prusa_gcode_backend.py`

- L204: self.send_gcode("G28", timeout=30.0)
- L228: parts = ["G1"]

### `core\system\hardware_information_exchange.py`

- L25: FORBIDDEN_GCODE_PREFIXES = ("G0", "G1", "G28", "G29", "M17", "M18", "M84", "M112")

### `core\system\hardware_test_controls.py`

- L88: [f"G1 Z{SAFE_RETRACT_Z:.2f} F{DEFAULT_Z_FEEDRATE:.0f}", "M400", "M114"],
- L97: f"G1 Z{SAFE_RETRACT_Z:.2f} F{DEFAULT_Z_FEEDRATE:.0f}",
- L99: f"G1 X{SAFE_CENTER_X:.2f} Y{SAFE_CENTER_Y:.2f} F{DEFAULT_XY_FEEDRATE:.0f}",
- L120: [f"G1 {axis.upper()}{target:.2f} F{feedrate:.0f}", "M400", "M114"],

### `core\system\mk4s_z_auto_approach.py`

- L60: "M17",
- L62: f"G1 Z{start_z:.2f} F600",
- L64: f"G1 X{x:.2f} Y{y:.2f} F1200",
- L94: commands.extend([f"G1 Z{z_value:.2f} F{feedrate:.0f}", "M400", "M114"])
- L96: commands.extend([f"G1 Z{safe_retract_z:.2f} F600", "M400", "M114"])
- L149: timeout = 90.0 if command.startswith("G1 ") or command == "M400" else 8.0
- L212: command = f"G1 Z{target_z:.2f} F300"
- L230: command = f"G1 Z{safe_z:.2f} F600"

### `docs\MK4S_BRINGUP_CHECKLIST.md`

- L20: - Run homing (`G28`) with clear workspace

### `docs\MK4S_BRINGUP_LOG_2026-06-09.md`

- L16: - G28 homing works

### `docs\PHASE1_CODE_MAP.md`

- L125: - tools\phase9_xy_10x10_topography_skeleton.py:365: f"G1 Z{CONTACT_Z:.2f} F60",
- L129: - tools\phase9_xy_3x3_topography_skeleton.py:69: move_and_wait(f"G1 Z{contact_z} F60", read_time=120)
- L138: - tools\phase9_x_line_topography_skeleton_v2.py:60: send(f"G1 Z{contact_z} F60", read_time=80)
- L150: - docs\versions\v0.14.0_phase9_6_robust_executor_2026-06-12\backup\phase9_xy_10x10_topography_skeleton.py:365: f"G1 Z{CONTACT_Z:.2f} F60",
- L167: - docs\PHASE1_CODE_MAP.md:116: - tools\phase9_xy_10x10_topography_skeleton.py:365: f"G1 Z{CONTACT_Z:.2f} F60",
- L171: - docs\PHASE1_CODE_MAP.md:120: - tools\phase9_xy_3x3_topography_skeleton.py:69: move_and_wait(f"G1 Z{contact_z} F60", read_time=120)
- L180: - docs\PHASE1_CODE_MAP.md:129: - tools\phase9_x_line_topography_skeleton_v2.py:60: send(f"G1 Z{contact_z} F60", read_time=80)
- L192: - docs\PHASE1_CODE_MAP.md:141: - docs\versions\v0.14.0_phase9_6_robust_executor_2026-06-12\backup\phase9_xy_10x10_topography_skeleton.py:365: f"G1 Z{CONTACT_Z:.2f} F60",
- L199: - core\system\mk4s_z_auto_approach.py:215: command = f"G1 Z{safe_z:.2f} F600"
- L204: - tools\phase9_xy_3x3_topography_skeleton.py:57: move_and_wait(f"G1 Z{safe_z} F600", read_time=60)
- L205: - tools\phase9_xy_3x3_topography_skeleton.py:81: move_and_wait(f"G1 Z{safe_z} F600", read_time=60)
- L207: - tools\phase9_x_line_topography_skeleton_v2.py:50: send(f"G1 Z{safe_z} F600", read_time=40)

### `docs\PHASE1_CODE_ONLY_MAP.md`

- L51: - core\system\hardware_test_controls.py:88: [f"G1 Z{SAFE_RETRACT_Z:.2f} F{DEFAULT_Z_FEEDRATE:.0f}", "M400", "M114"],
- L52: - core\system\hardware_test_controls.py:97: f"G1 Z{SAFE_RETRACT_Z:.2f} F{DEFAULT_Z_FEEDRATE:.0f}",
- L59: - core\system\mk4s_z_auto_approach.py:62: f"G1 Z{start_z:.2f} F600",
- L60: - core\system\mk4s_z_auto_approach.py:79: commands.extend([f"G1 Z{z_value:.2f} F{feedrate:.0f}", "M400", "M114"])
- L61: - core\system\mk4s_z_auto_approach.py:81: commands.extend([f"G1 Z{safe_retract_z:.2f} F600", "M400", "M114"])
- L67: - core\system\mk4s_z_auto_approach.py:197: command = f"G1 Z{target_z:.2f} F300"
- L71: - core\system\mk4s_z_auto_approach.py:215: command = f"G1 Z{safe_z:.2f} F600"
- L86: - tools\phase8_z_safe_visible_move.py:31: send("G1 Z120 F600", wait=6, read_time=6)
- L87: - tools\phase8_z_safe_visible_move.py:34: send("G1 Z100 F600", wait=6, read_time=6)
- L88: - tools\phase9_auto_step_z_approach_foam.py:31: send("G1 Z120 F600", wait=6)
- L91: - tools\phase9_auto_step_z_approach_foam.py:42: send(f"G1 Z{z} F60", wait=3)
- L93: - tools\phase9_auto_step_z_approach_foam.py:48: send("G1 Z120 F600", wait=8)

### `docs\PHASE1_Z_CLIPBOARD_REPORT.txt`

- L724: 204:         self.send_gcode("G28", timeout=30.0)
- L739: 204:         self.send_gcode("G28", timeout=30.0)
- L770: 60:         "M17",
- L772: 62:         f"G1 Z{start_z:.2f} F600",
- L774: 64:         f"G1 X{x:.2f} Y{y:.2f} F1200",
- L783: 60:         "M17",
- L785: 62:         f"G1 Z{start_z:.2f} F600",
- L787: 64:         f"G1 X{x:.2f} Y{y:.2f} F1200",
- L802: 79:         commands.extend([f"G1 Z{z_value:.2f} F{feedrate:.0f}", "M400", "M114"])
- L804: 81:         commands.extend([f"G1 Z{safe_retract_z:.2f} F600", "M400", "M114"])
- L809: 62:         f"G1 Z{start_z:.2f} F600",
- L811: 64:         f"G1 X{x:.2f} Y{y:.2f} F1200",

### `docs\PHASE1_Z_GUI_FUNCTIONS.md`

- L1103: 204:         self.send_gcode("G28", timeout=30.0)
- L1173: 228:         parts = ["G1"]
- L1280: - `core\system\hardware_test_controls.py`:88: [f"G1 Z{SAFE_RETRACT_Z:.2f} F{DEFAULT_Z_FEEDRATE:.0f}", "M400", "M114"],
- L1281: - `core\system\hardware_test_controls.py`:97: f"G1 Z{SAFE_RETRACT_Z:.2f} F{DEFAULT_Z_FEEDRATE:.0f}",
- L1295: - `core\system\mk4s_z_auto_approach.py`:215: command = f"G1 Z{safe_z:.2f} F600"

### `docs\PHASE_2_1E_MAIN_SYSTEM_DRY_RUN.md`

- L41: - `G1`
- L42: - `G28`

### `docs\ROADMAP.md`

- L7: - Validate explicit `G28` homing and bounded `G1` moves

### `docs\Tipp_order.txt`

- L55: - **Thorlabs PTG10 Tungsten Probe Tip**
- L160: | 5 | Thorlabs PTG10 Tungsten Tip | 1 | Optional ultra‑sharp tip |

### `docs\versions\v0.13.0_phase7_general_system_initialization_2026-06-11\backup\test_hardware_startup_initializer.py`

- L10: assert "G28" not in READONLY_STARTUP_COMMANDS
- L11: assert "G1" not in READONLY_STARTUP_COMMANDS
- L12: assert "M17" not in READONLY_STARTUP_COMMANDS

### `docs\versions\v0.14.0_phase9_6_robust_executor_2026-06-12\backup\phase9_xy_10x10_topography_skeleton.py`

- L278: executor.move_and_wait(f"G1 Z{SAFE_RETRACT_Z:.2f} F600", move_timeout_s=90, wait_timeout_s=180)
- L280: f"G1 X{SAFE_CENTER_X:.2f} Y{SAFE_CENTER_Y:.2f} F600",
- L344: executor.send("M17", timeout_s=45)
- L346: executor.move_and_wait(f"G1 Z{SAFE_RETRACT_Z:.2f} F600", move_timeout_s=90, wait_timeout_s=180)
- L358: f"G1 X{x:.2f} Y{y:.2f} F600",
- L365: f"G1 Z{CONTACT_Z:.2f} F60",
- L391: executor.move_and_wait(f"G1 Z{SAFE_RETRACT_Z:.2f} F600", move_timeout_s=90, wait_timeout_s=180)

### `docs\versions\v0.15.0_hardware_information_layer_and_crtouch_plan_2026-06-12\backup\hardware_information_exchange.py`

- L25: FORBIDDEN_GCODE_PREFIXES = ("G0", "G1", "G28", "G29", "M17", "M18", "M84", "M112")

### `docs\versions\v0.15.0_hardware_information_layer_and_crtouch_plan_2026-06-12\backup\test_hardware_information_exchange.py`

- L26: for command in ["G1 X125", "G28", "M17", "M112"]:

### `docs\versions\v0.16.0_ht3_hardware_test_controls_2026-06-12\backup\hardware_test_controls.py`

- L88: [f"G1 Z{SAFE_RETRACT_Z:.2f} F{DEFAULT_Z_FEEDRATE:.0f}", "M400", "M114"],
- L97: f"G1 Z{SAFE_RETRACT_Z:.2f} F{DEFAULT_Z_FEEDRATE:.0f}",
- L99: f"G1 X{SAFE_CENTER_X:.2f} Y{SAFE_CENTER_Y:.2f} F{DEFAULT_XY_FEEDRATE:.0f}",
- L120: [f"G1 {axis.upper()}{target:.2f} F{feedrate:.0f}", "M400", "M114"],

### `docs\versions\v0.16.0_ht3_hardware_test_controls_2026-06-12\backup\test_hardware_test_controls.py`

- L36: assert plan.commands[0] == f"G1 Z{SAFE_RETRACT_Z:.2f} F300"
- L37: assert plan.commands[2] == f"G1 X{SAFE_CENTER_X:.2f} Y{SAFE_CENTER_Y:.2f} F600"
- L50: assert plan.commands[0] == "G1 X130.00 F600"
- L78: assert "G1 Z120.00 F300" in result.stdout
- L79: assert "G1 X125.00 Y105.00 F600" in result.stdout
- L86: commands=["G1 Z120.00 F300", "M400"],

### `docs\versions\v0.22.0_essential_initialize_and_mk4s_z_auto_approach_2026-06-12\mk4s_z_auto_approach.py`

- L42: "M17",
- L44: f"G1 Z{start_z:.2f} F600",
- L46: f"G1 X{x:.2f} Y{y:.2f} F1200",
- L53: commands.extend([f"G1 Z{z_value:.2f} F{feedrate:.0f}", "M400", "M114"])
- L55: commands.extend([f"G1 Z{safe_retract_z:.2f} F600", "M400", "M114"])
- L107: timeout = 90.0 if command.startswith("G1 ") or command == "M400" else 8.0

### `docs\versions\v0.22.0_essential_initialize_and_mk4s_z_auto_approach_2026-06-12\test_mk4s_z_auto_approach.py`

- L7: assert "G1 Z120.00 F600" in commands
- L8: assert "G1 X125.00 Y105.00 F1200" in commands
- L9: assert "G1 Z56.00 F60" in commands

### `docs\versions\v0.24.0_connect_approach_measurement_main_page_2026-06-12\mk4s_z_auto_approach.py`

- L60: "M17",
- L62: f"G1 Z{start_z:.2f} F600",
- L64: f"G1 X{x:.2f} Y{y:.2f} F1200",
- L79: commands.extend([f"G1 Z{z_value:.2f} F{feedrate:.0f}", "M400", "M114"])
- L81: commands.extend([f"G1 Z{safe_retract_z:.2f} F600", "M400", "M114"])
- L134: timeout = 90.0 if command.startswith("G1 ") or command == "M400" else 8.0
- L197: command = f"G1 Z{target_z:.2f} F300"
- L215: command = f"G1 Z{safe_z:.2f} F600"

### `docs\versions\v0.24.0_connect_approach_measurement_main_page_2026-06-12\test_mk4s_z_auto_approach.py`

- L7: assert "G1 Z120.00 F600" in commands
- L8: assert "G1 X125.00 Y105.00 F1200" in commands
- L9: assert "G1 Z56.00 F60" in commands
- L26: assert "G1 Z57.50 F60" in commands

### `tests\test_hardware_information_exchange.py`

- L26: for command in ["G1 X125", "G28", "M17", "M112"]:

### `tests\test_hardware_startup_initializer.py`

- L10: assert "G28" not in READONLY_STARTUP_COMMANDS
- L11: assert "G1" not in READONLY_STARTUP_COMMANDS
- L12: assert "M17" not in READONLY_STARTUP_COMMANDS

### `tests\test_hardware_test_controls.py`

- L36: assert plan.commands[0] == f"G1 Z{SAFE_RETRACT_Z:.2f} F300"
- L37: assert plan.commands[2] == f"G1 X{SAFE_CENTER_X:.2f} Y{SAFE_CENTER_Y:.2f} F600"
- L50: assert plan.commands[0] == "G1 X130.00 F600"
- L78: assert "G1 Z120.00 F300" in result.stdout
- L79: assert "G1 X125.00 Y105.00 F600" in result.stdout
- L86: commands=["G1 Z120.00 F300", "M400"],

### `tests\test_mk4s_z_auto_approach.py`

- L7: assert "G1 Z120.00 F600" in commands
- L8: assert "G1 X125.00 Y105.00 F1200" in commands
- L9: assert "G1 Z56.00 F60" in commands
- L26: assert "G1 Z57.50 F60" in commands

### `tests\test_mk4s_z_auto_approach_no_forced_z60.py`

- L21: if command.startswith("G1 Z"):

### `tests\test_web_operator_console.py`

- L342: assert "G1" not in plan
- L343: assert "G28" not in plan

## dry_run_simulation

### `ROADMAP_SPM_PRUSA.md`

- L23: The system should be able to scan surfaces, display measured or simulated shapes in software, and later also print or reproduce shapes.
- L51: If motion is real but values are simulated, label it as: Real MK4S motion with simulated measurement values.
- L137: 4. Keep real/simulated measurement labels clear.

### `config\spm_mk4s_config.json`

- L37: "feedback": "MK4S Z height is used for clearance; fine SPM feedback is simulated until the later Z scanner is installed",
- L68: "feedback": "contact threshold is planned later; current tests use original MK4S Z clearance plus dry-run feedback",
- L84: "description": "AFM-style educational template using original MK4S motion; force feedback is simulated for now.",
- L99: "feedback": "constant-force concept is simulated until the future force/Z subsystem is installed",
- L115: "description": "STM-style educational template using original MK4S motion; tunneling-current channel is simulated for now.",
- L130: "feedback": "constant-current concept is simulated until STM electronics and fine Z are installed",
- L161: "simulated_z_signal": 0.0,

### `core\acquisition\channels.py`

- L30: name = "simulated_surface"

### `core\acquisition\raster_stream.py`

- L72: f"Current channel: simulated surface signal\n"

### `core\ai\academic_ai_client.py`

- L35: mode="configured" if configured else "stub_not_configured",
- L37: safety_rule="AI may recommend approach, scan, simulation, or diagnosis steps, but cannot execute machine motion directly.",
- L54: "Use dry-run or simulation mode first.",
- L71: elif "simulation" in normalized or "surface" in normalized or "demo" in normalized:
- L73: "Use the simulation layer to generate expected topography first.",
- L74: "Keep simulation parameters separate from real hardware parameters.",
- L75: "Use the same scan profile for simulation and real scan comparison.",
- L76: "Show simulation output in the Live View window.",

### `core\application\cli_scan_launcher.py`

- L71: dry_run: bool = False,
- L98: if dry_run:
- L99: command.insert(2, "--dry-run")
- L117: build_hardware_command(profile, output_file, dry_run=True),
- L129: parser.add_argument("--dry-run", action="store_true")
- L166: if args.dry_run:
- L189: print("Use --dry-run for validation only.")

### `core\application\gui_scan_launcher.py`

- L230: self.dry_run_btn = QPushButton("Demo Scan - No Hardware Movement")
- L231: self.dry_run_btn.clicked.connect(self.run_dry_scan)
- L239: # Safe Z-control dry-run driver
- L243: self.z_driver = ZDriverArduino(dry_run=True)
- L245: self.z_status_label = QLabel("Z dry-run status: Disconnected")
- L431: "Generate a scan preview using the dry-run pipeline. "
- L483: scan_execution_layout.addWidget(self.dry_run_btn)
- L495: # Z-control dry-run tools
- L504: z_height_layout.addRow("Z dry-run test position:", self.z_test_position)
- L616: measurement_actions_layout.addWidget(self.dry_run_btn)
- L936: "- Current approach and feedback tools are dry-run training aids.\n\n"
- L944: "7. Enable real motion only when the MK4S path is clear and the dry-run result is acceptable.\n"

### `core\application\hardware_information_cli.py`

- L3: Default mode is dry-run planning. Use --real to open the confirmed serial port

### `core\application\hardware_test_control_cli.py`

- L3: Default mode is dry-run planning. Real movement requires --execute.

### `core\education\config_loader.py`

- L50: "feedback": "default Z dry-run profile",

### `core\education\safe_raster.py`

- L14: simulated_z_signal: float
- L89: simulated_z_signal=float(z_signal),

### `core\hardware\hardware_command_bus.py`

- L20: """Safe simulated command bus before connecting real hardware."""

### `core\motion\motion_backend.py`

- L10: - simulated

### `core\scan\controller\scan_manager.py`

- L7: def __init__(self, scan_mode_instance, use_simulation=True):
- L11: use_simulation (bool): If True, operate in simulation mode; otherwise, connect to hardware.
- L14: self.use_simulation = use_simulation

### `core\scan\modes\afm_contact_mode.py`

- L26: self.simulated_surface = None
- L30: self.simulated_surface = self._generate_simulated_surface()
- L56: def _generate_simulated_surface(self):
- L66: return self.simulated_surface[iy, ix]

### `core\scan\modes\afm_noncontact_mode.py`

- L29: self.simulated_surface = None
- L33: self.simulated_surface = self._generate_simulated_amplitude_map()
- L60: def _generate_simulated_amplitude_map(self):
- L70: return self.simulated_surface[iy, ix]
- L73: # Simple inverse mapping for simulation purposes

### `core\scan\modes\profiling_mode.py`

- L29: self.simulated_profile = None
- L33: self.simulated_profile = self._generate_simulated_profile()
- L58: def _generate_simulated_profile(self):
- L66: return self.simulated_profile[i]

### `core\scan\modes\stm_mode.py`

- L11: Implements STM scanning behavior (simulated or hardware mode).
- L36: self.simulated_surface = None
- L49: self.simulated_surface = self._generate_simulated_surface()
- L75: def _generate_simulated_surface(self):
- L87: Approximate the Z-height for a given (x, y) from the simulated surface.
- L91: return self.simulated_surface[iy, ix]

### `core\system\hardware_diagnostics.py`

- L124: "Approach/feedback controls are dry-run training until the later Z subsystem is mounted and assigned a confirmed port.",

### `core\system\mk4s_z_auto_approach.py`

- L17: dry_run: bool
- L130: dry_run=True,
- L157: dry_run=False,

### `core\system\workstation_initializer.py`

- L34: current dry-run Z scanner layer. It does not enable real motion.

### `core\web\operator_console_server.py`

- L13: from core.web.spm_scan_simulation import build_scan_line, profile_from_query, scan_profile_payload
- L14: from core.web.system_control import dry_run_startup_plan, system_close, system_off, system_on, system_status
- L92: mode = query.get("mode", ["dry_run"])[0]
- L104: if route == "/api/system/dry-run":
- L105: self._send_json(dry_run_startup_plan())
- L116: "mk4s": "not_connected_stub",
- L117: "z_scanner": "not_connected_stub",
- L118: "xy_scanner": "simulation_scan_model",
- L122: "default_mode": "simulation_stub",
- L126: "start_pause_stop": "simulation_shell",
- L127: "default_center": "simulation_shell",

### `core\web\spm_scan_simulation.py`

- L1: """SPM raster scan simulation model for the web operator console."""
- L45: def simulated_surface_height(x: float, y: float, profile: WebScanProfile) -> float:
- L88: surface_height = simulated_surface_height(x, y, profile)
- L110: "height_source": "simulated_z_feedback_minus_setpoint",

### `core\web\system_control.py`

- L5: Default behavior is dry-run only.
- L23: mode: str = "dry_run"
- L26: dry_run_plan: list[str] = field(default_factory=list)
- L55: "default_mode": "dry_run",
- L60: "dry_run_plan": list(STATE.dry_run_plan),
- L65: def system_on(mode: str = "dry_run") -> dict[str, Any]:
- L66: """Start the main system in dry-run or locked hardware mode."""
- L67: requested_mode = (mode or "dry_run").strip().lower()
- L69: if requested_mode not in {"dry_run", "hardware"}:
- L70: requested_mode = "dry_run"
- L76: STATE.mode = "dry_run"
- L78: STATE.dry_run_plan = list(READ_ONLY_STARTUP_PLAN)

### `core\z_control\z_driver_arduino_safe.py`

- L12: Default mode is dry_run=True.
- L13: In dry-run mode, no real serial connection is opened and no hardware moves.
- L16: def __init__(self, port: str = "COM5", baudrate: int = 115200, dry_run: bool = True):
- L19: self.dry_run = dry_run
- L26: if self.dry_run:
- L37: if self.dry_run:
- L55: if self.dry_run:
- L109: if self.dry_run:
- L115: return self.connected and self.dry_run
- L122: "dry_run": self.dry_run,

### `core\z_control\z_driver_simulated.py`

- L1: # z_driver_simulated.py

### `core\z_control\z_interface.py`

- L4: from core.z_control.z_driver_simulated import SimulatedZDriver
- L12: def get_z_driver(mode='simulated'):
- L17: mode (str): 'simulated' or 'hardware'
- L20: Instance of Z-driver (simulated or hardware).

### `core\z_control\z_simulator.py`

- L8: # placeholder simulation logic

### `data\directional_demo_scan_2026_06_11.metadata.json`

- L2: "channel": "simulated_surface",

### `data\educational_spm_clean_flow_dry_test_2026_06_11.metadata.json`

- L2: "channel": "simulated_surface",

## z_control

### `README.md`

- L10: - Simulated Z driver works
- L19: - Z: 5 to 50
- L46: - Arduino/Z-control hardware is not detected yet.

### `ROADMAP_SPM_PRUSA.md`

- L42: Bug 1 - Z setpoint does not follow the entered number.
- L43: Observed: values like 0, 10, and 2 are entered, but Z stays around 60 mm.
- L44: Required: trace Z through GUI input, scan profile, validation, scan runner, MK4S command generation, and display.
- L63: 1. Fix Z setpoint handling.
- L108: Hardware movement must respect safe X, Y, and Z limits.
- L134: 1. Fix Z setpoint handling.

### `config\spm_hardware_initialized_profile.json`

- L32: "z_approach_allowed_during_initialization": false
- L70: "tested_command": "G1 Z120 followed by G1 Z100",
- L71: "software_coordinate_change": "Z 100.00 -> Z 120.00 -> Z 100.00",
- L72: "observed_physical_motion": "up during Z increase, down during return",
- L77: "z_approach_reference": {
- L78: "phase": "Phase 9.2 manual foam approach",
- L86: "approach_position": {
- L93: "safe_retract_z": 120.0,
- L95: "safety_note": "Manual approach only. Automatic hit-stop/contact detection not yet implemented.",
- L96: "auto_step_approach_confirmed": {
- L98: "method": "software-controlled step approach",
- L117: "safe_retract_z": 120.0,

### `config\spm_mk4s_config.json`

- L37: "feedback": "MK4S Z height is used for clearance; fine SPM feedback is simulated until the later Z scanner is installed",
- L38: "approach_start": 20,
- L39: "approach_target": 17,
- L40: "retract_target": 20,
- L43: "auto_approach_ready": true,
- L48: "z_stage": "Original Prusa MK4S Z axis",
- L68: "feedback": "contact threshold is planned later; current tests use original MK4S Z clearance plus dry-run feedback",
- L69: "approach_start": 30,
- L70: "approach_target": 18,
- L71: "retract_target": 30,
- L74: "auto_approach_ready": false,
- L79: "z_stage": "Original Prusa MK4S Z axis now; fine Z scanner planned later",

### `core\acquisition\raster_stream.py`

- L47: f"Z/signal range: {low:.4f} to {high:.4f}\n"
- L68: "Z / Signal Feedback\n"
- L75: f"Z source: synthetic readback until CR-Touch contact probe is mounted"

### `core\ai\academic_ai_client.py`

- L37: safety_rule="AI may recommend approach, scan, simulation, or diagnosis steps, but cannot execute machine motion directly.",
- L51: if "approach" in normalized or "z" in normalized:
- L53: "Confirm MK4S position readback before any Z move.",
- L55: "Use small Z steps near the surface.",
- L57: "Log every approach/retract command.",
- L67: "Only enable real scan after Z and XY status are valid.",

### `core\application\gui_scan_launcher.py`

- L51: from core.system.mk4s_z_auto_approach import confirmed_approach_reference, run_mk4s_z_auto_approach, run_mk4s_z_manual_step, run_mk4s_z_safe_retract
- L57: from core.z_control.z_driver_arduino_safe import ZDriverArduino
- L93: self.z_approached = False
- L201: self.open_z_tools_btn = QPushButton("Z / APPROACH")
- L239: # Safe Z-control dry-run driver
- L241: # They only test the Phase 5.1 Arduino/Z-control software path.
- L243: self.z_driver = ZDriverArduino(dry_run=True)
- L245: self.z_status_label = QLabel("Z dry-run status: Disconnected")
- L250: self.z_approach_start = QLineEdit("20")
- L251: self.z_approach_target = QLineEdit("17")
- L252: self.z_retract_start = QLineEdit("17")
- L253: self.z_retract_target = QLineEdit("20")

### `core\application\hardware_test_console_gui.py`

- L96: "connection, endstops, temperature/status, and XYZ position before suggesting the next action."
- L128: position_btn = QPushButton("Read XYZ")
- L154: self.position_status = QLabel("XYZ position: not checked")
- L164: read_xyz_btn = QPushButton("Read Current XYZ - Real Safe")
- L226: safe_position_btn = QPushButton("Read Current XYZ - Real Safe")
- L239: "Z_STEP_UP",
- L240: "Z_STEP_DOWN",
- L374: QMessageBox.critical(self, "XYZ position read failed", str(error))
- L388: self.position_status.setText("XYZ position: read response did not include coordinates")
- L392: f"XYZ position: X={position['x']:.2f} mm | Y={position['y']:.2f} mm | Z={position['z']:.2f} mm"

### `core\application\workstation_status.py`

- L33: f"Z {limits['z'][0]}-{limits['z'][1]}"

### `core\education\config_loader.py`

- L50: "feedback": "default Z dry-run profile",
- L51: "approach_start": config["scan_area"]["z"],
- L52: "approach_target": config["scan_area"]["z"],
- L53: "retract_target": config["scan_area"]["z"],
- L56: "auto_approach_ready": False,
- L61: "z_stage": "configured Z controller",

### `core\education\safe_raster.py`

- L79: """Create one raster data row from target position, printer state, and Z signal."""

### `core\motion\parking.py`

- L8: """Park MK4S by retracting Z first, then moving XY to the parking corner."""

### `core\motion\prusa_gcode_backend.py`

- L86: Expected tokens include X:.. Y:.. Z:.. (E optional).
- L90: for axis in ("X", "Y", "Z", "E"):
- L100: ("Z", z, self.z_limits),
- L234: parts.append(f"Z{z}")

### `core\scan\modes\afm_contact_mode.py`

- L6: from core.z_control.z_interface import get_z_driver
- L19: self.z_driver = get_z_driver(hardware_mode)
- L33: self.z_driver.initialize()
- L38: self.z_driver.set_z_position(z)
- L54: self.z_driver.shutdown()
- L60: Z = 1.5 * np.sin(3 * np.pi * X / self.x_range) * np.sin(2 * np.pi * Y / self.y_range)
- L61: return Z

### `core\scan\modes\afm_noncontact_mode.py`

- L7: from core.z_control.z_interface import get_z_driver
- L22: self.z_driver = get_z_driver(hardware_mode)
- L36: self.z_driver.initialize()
- L42: self.z_driver.set_z_position(z)
- L58: self.z_driver.shutdown()
- L64: Z = 1.0 - 0.2 * np.cos(2 * np.pi * X / self.x_range) * np.cos(2 * np.pi * Y / self.y_range)
- L65: return Z

### `core\scan\modes\base_scan_mode.py`

- L6: from core.z_control.z_interface import get_z_driver

### `core\scan\modes\profiling_mode.py`

- L6: from core.z_control.z_interface import get_z_driver
- L23: self.z_driver = get_z_driver(hardware_mode)
- L36: self.z_driver.initialize()
- L41: self.z_driver.set_z_position(height)
- L56: self.z_driver.shutdown()

### `core\scan\modes\stm_mode.py`

- L6: from core.z_control.z_interface import get_z_driver
- L17: self.z_driver = get_z_driver(hardware_mode)
- L52: self.z_driver.initialize()
- L57: self.z_driver.set_z_position(z)
- L73: self.z_driver.shutdown()
- L82: Z = 2 * np.sin(2 * np.pi * X / self.x_range) * np.cos(2 * np.pi * Y / self.y_range)
- L83: return Z
- L87: Approximate the Z-height for a given (x, y) from the simulated surface.

### `core\system\hardware_diagnostics.py`

- L119: name="Future fine Z scanner",
- L121: message="Fine Z scanner communication is not part of the current MK4S-original hardware test.",
- L123: "Current hardware test uses the original Prusa MK4S X/Y/Z motion system.",
- L124: "Approach/feedback controls are dry-run training until the later Z subsystem is mounted and assigned a confirmed port.",
- L134: f"Machine limits: X {limits['x']}, Y {limits['y']}, Z {limits['z']}",
- L135: f"Recommended SPM-safe limits: X {safe_limits['x']}, Y {safe_limits['y']}, Z {safe_limits['z']}",
- L140: f"Z {scan_area['z']}, "

### `core\system\hardware_initialized_profile.py`

- L33: and rules["z_approach_allowed_during_initialization"] is False

### `core\system\hardware_profile.py`

- L40: z=AxisLimit("Z", safe_limits["z"][0], safe_limits["z"][1], limits["z"][0], limits["z"][1]),
- L48: "For SPM work, keep routine scans near 46..54 mm and Z near 20 mm until the probe is mounted."
- L68: "Official maxima tested: X250, Y210, Z220\n"
- L70: "Z0 is not auto-tested because it is collision-sensitive.\n\n"
- L74: f"Z min {self.z.firmware_min:g} / max {self.z.firmware_max:g}\n"
- L79: f"Z min {self.z.spm_safe_min:g} / max {self.z.spm_safe_max:g}"
- L88: f"Z {self.z.firmware_min:g}..{self.z.firmware_max:g}. "

### `core\system\hardware_test_controls.py`

- L26: "Z_STEP_UP",
- L27: "Z_STEP_DOWN",
- L32: SAFE_RETRACT_Z = 120.0
- L35: DEFAULT_Z_FEEDRATE = 300.0
- L80: current_position = current_position or {"x": SAFE_CENTER_X, "y": SAFE_CENTER_Y, "z": SAFE_RETRACT_Z}
- L83: return HardwareTestPlan(action_clean, ["M114"], False, "Read-only XYZ position query.")
- L88: [f"G1 Z{SAFE_RETRACT_Z:.2f} F{DEFAULT_Z_FEEDRATE:.0f}", "M400", "M114"],
- L90: "Retract Z to the confirmed safe height.",
- L97: f"G1 Z{SAFE_RETRACT_Z:.2f} F{DEFAULT_Z_FEEDRATE:.0f}",
- L104: "Retract Z first, then return XY to foam center.",
- L112: "Z_STEP_UP": ("z", step_mm, DEFAULT_Z_FEEDRATE),
- L113: "Z_STEP_DOWN": ("z", -step_mm, DEFAULT_Z_FEEDRATE),

### `core\system\mk4s_z_auto_approach.py`

- L1: """Focused MK4S Z auto-approach sequence for the Educational SPM project."""
- L15: class ZAutoApproachResult:
- L25: class ZManualMoveResult:
- L33: def confirmed_approach_reference() -> dict:
- L35: return profile["hardware_initialized_profile"]["z_approach_reference"]
- L38: def planned_auto_approach_commands(
- L41: retract_after: bool = False,
- L43: reference = confirmed_approach_reference()
- L44: auto = reference["auto_step_approach_confirmed"]
- L52: raise ValueError(f"Approach target Z {stop_z:.2f} is below safe minimum Z {minimum_z:.2f}")
- L54: raise ValueError(f"Approach target Z {stop_z:.2f} is above start Z {start_z:.2f}")
- L56: safe_retract_z = float(auto["safe_retract_z"])

### `core\system\smart_hardware_assessment.py`

- L23: match = re.search(r"X:\s*(-?\d+(?:\.\d+)?)\s+Y:\s*(-?\d+(?:\.\d+)?)\s+Z:\s*(-?\d+(?:\.\d+)?)", joined)
- L76: f"XYZ position inside confirmed limits: X={position['x']:.2f}, Y={position['y']:.2f}, Z={position['z']:.2f}."
- L80: details.append("XYZ position was read, but one axis is outside the confirmed software limits.")
- L82: details.append("Position command responded, but XYZ coordinates were not parsed.")
- L84: details.append("XYZ position was not confirmed.")

### `core\system\workstation_initializer.py`

- L26: z_driver,
- L34: current dry-run Z scanner layer. It does not enable real motion.
- L42: if not getattr(z_driver, "connected", False):
- L43: z_ready = bool(z_driver.connect())
- L48: ready_state = "SYSTEM READY" if passed else "INITIALIZATION FAILED"
- L50: "System ready. Next: use Z Scanner controls for manual move, auto approach, or retract."
- L58: f"Z scanner layer: {'READY' if z_ready else 'NOT READY'}",

### `core\web\operator_console_server.py`

- L36: "name": "Z scanner / Academic AI advisory layer",
- L38: "purpose": "Advisory-only AI assistant and Z scanner shell.",
- L50: "purpose": "Connect proven old Z approach, XY raster, CSV, PNG, and Gwyddion export services.",
- L56: "purpose": "Finalize connect, initialize, approach, scan, export, park, and shutdown workflow.",
- L125: "approach_required_before_scan": True,

### `core\z_control\crtouch_probe_plan.py`

- L8: probe_name: str = "CR-Touch contact Z probe"
- L32: "CR-Touch Z probe safety: use slow Z movement, verify repeatable trigger, "
- L33: "avoid hard collisions, and keep the real Z path disabled until wiring, "
- L41: "smooth guide motion without sticking before any software-controlled approach."

### `core\z_control\z_driver_arduino.py`

- L1: # z_driver_arduino.py
- L3: class ArduinoZDriver:

### `core\z_control\z_driver_arduino_safe.py`

- L1: # File: core/z_control/z_driver_arduino_safe.py
- L8: class ZDriverArduino:
- L10: Safe Arduino Z-control driver for Phase 5.1.
- L50: raise RuntimeError("Z driver is not connected. Connect first.")
- L56: print(f"[DRY RUN] Move to Z={self.last_z_position}")
- L60: "Real Z movement is intentionally disabled in this safe Phase 5.1 driver."
- L63: def approach(self, start_z: float, target_z: float, step: float = 1.0) -> None:
- L65: raise RuntimeError("Z driver is not connected. Connect first.")
- L76: self.last_command = "approach"
- L77: print(f"[DRY RUN] Approach from Z={start_z} to Z={target_z} with step={step}")
- L82: print(f"[DRY RUN] Approach step Z={current}")
- L85: def retract(self, start_z: float, target_z: float, step: float = 1.0) -> None:

### `core\z_control\z_driver_simulated.py`

- L1: # z_driver_simulated.py
- L5: class SimulatedZDriver:

## scan

### `README.md`

- L9: - Config-based safe raster scan works

### `ROADMAP_SPM_PRUSA.md`

- L19: The project uses the Prusa MK4S hardware as a scanning probe microscope style platform.
- L21: The realistic goal is micrometer-scale scanning, or the best possible resolution within the mechanical and sensor limits of the Prusa MK4S.
- L23: The system should be able to scan surfaces, display measured or simulated shapes in software, and later also print or reproduce shapes.
- L44: Required: trace Z through GUI input, scan profile, validation, scan runner, MK4S command generation, and display.
- L49: Bug 3 - Real MK4S motion does not update the main scan window properly.
- L50: Required: real hardware scan loop must update the main scan display live.
- L65: 3. Connect real MK4S scan loop to the live main scan window.
- L74: 4. Add generate_surface(scan_profile, shape_profile).
- L79: 2 corners -> line or ridge
- L97: Future targets: STL, OBJ, image-to-heightmap, scanned object to printable object.
- L101: AI may suggest scan settings or shape parameters.
- L102: Local software must validate all AI output before preview, scan, or print.

### `config\spm_hardware_initialized_profile.json`

- L31: "scan_allowed_during_initialization": false,
- L62: "note": "Use this physical direction mapping later for raster scan planning and GUI labels.",

### `config\spm_mk4s_config.json`

- L20: "scan_mode_presets": {
- L22: "description": "Educational SPM default using the original Prusa MK4S motion system and synthetic topography readback.",
- L23: "scan_area": {
- L37: "feedback": "MK4S Z height is used for clearance; fine SPM feedback is simulated until the later Z scanner is installed",
- L54: "scan_area": {
- L79: "z_stage": "Original Prusa MK4S Z axis now; fine Z scanner planned later",
- L85: "scan_area": {
- L110: "z_stage": "Original Prusa MK4S Z axis now; fine Z scanner planned later",
- L116: "scan_area": {
- L141: "z_stage": "Original Prusa MK4S Z axis now; fine Z scanner planned later",
- L146: "scan_area": {
- L160: "safe_raster": {

### `core\__init__.py`

- L1: from . import scan

### `core\acquisition\channels.py`

- L26: """Read one synchronized sensor sample at the current scan position."""

### `core\acquisition\raster_stream.py`

- L6: from tools.plot_safe_raster import load_raster_csv
- L23: def latest_line(self) -> list[float]:
- L34: def line_scan_summary(self) -> str:
- L35: if not self.latest_line:
- L36: return "1D Line Scan\nNo line data loaded."
- L44: f"Latest Y line: {latest_y:.3f}\n"
- L46: f"Latest line points: {len(self.latest_line)}\n"
- L48: f"Last line preview: {', '.join(f'{value:.3f}' for value in _sample_values(self.latest_line, 12))}\n"
- L49: f"Profile: {self.line_profile_bar()}"
- L52: def topography_summary(self) -> str:
- L61: f"{self.topography_map_text()}"
- L78: def line_profile_bar(self) -> str:

### `core\acquisition\scan_session.py`

- L8: from core.education.scan_profile import ScanProfile
- L11: def build_scan_session_metadata(
- L25: "scan_profile": asdict(profile),
- L33: def write_scan_session_metadata(
- L43: metadata = build_scan_session_metadata(

### `core\acquisition\__init__.py`

- L1: """Acquisition and scan-readback helpers for the SPM workstation."""

### `core\ai\academic_ai_client.py`

- L37: safety_rule="AI may recommend approach, scan, simulation, or diagnosis steps, but cannot execute machine motion directly.",
- L61: elif "scan" in normalized or "xy" in normalized or "raster" in normalized:
- L63: "Start with a small scan area inside the safe XY envelope.",
- L65: "Preview the raster path before real movement.",
- L67: "Only enable real scan after Z and XY status are valid.",
- L73: "Use the simulation layer to generate expected topography first.",
- L75: "Use the same scan profile for simulation and real scan comparison.",

### `core\application\cli_scan_launcher.py`

- L13: get_safe_raster_config,
- L15: from core.education.scan_profile import (
- L18: validate_scan_profile,
- L22: def build_scan_profile_from_config(config: dict, mode: str) -> ScanProfile:
- L23: scan_area = config["scan_area"]
- L27: x_min=scan_area["x_min"],
- L28: x_max=scan_area["x_max"],
- L29: y_min=scan_area["y_min"],
- L30: y_max=scan_area["y_max"],
- L31: z=scan_area["z"],
- L32: x_resolution=scan_area["x_resolution"],
- L33: y_resolution=scan_area["y_resolution"],

### `core\application\gui_scan_launcher.py`

- L39: from core.acquisition.raster_stream import load_raster_frame
- L41: from core.education.config_loader import load_config, get_safe_feedrates, get_scan_mode_preset
- L42: from core.education.scan_profile import (
- L46: validate_scan_profile,
- L62: # Safe GUI wrapper around the verified CLI scan launcher
- L89: self.scan_viewers = []
- L94: self.scan_stop_requested = False
- L95: self.scan_pause_requested = False
- L96: self.live_scan_timer = QTimer(self)
- L97: self.live_scan_timer.timeout.connect(self.advance_live_scan)
- L98: self.live_scan_points = []
- L99: self.live_scan_index = 0

### `core\application\hardware_command_cli.py`

- L10: No scan commands.

### `core\application\hardware_information_cli.py`

- L46: for line in result.response_lines:
- L47: print(line)

### `core\application\hardware_startup_cli.py`

- L18: for line in command_result.response_lines:
- L19: print(line)

### `core\application\hardware_test_console_gui.py`

- L300: + " | ".join(result.response_lines)
- L303: self.update_position_status(result.response_lines)
- L330: + " | ".join(result.response_lines)
- L333: self.update_position_status(result.response_lines)
- L380: + " | ".join(result.response_lines)
- L383: self.update_position_status(result.response_lines)
- L385: def update_position_status(self, response_lines: list[str]) -> None:
- L386: position = extract_xyz(response_lines)

### `core\application\workstation_status.py`

- L13: scan_profile_valid: bool = False
- L14: last_scan_mode: str = "IDLE"
- L20: acquisition_status: str = "waiting for scan data"
- L35: last_output_file=str(config["safe_raster"]["output_file"]),
- L39: self.scan_profile_valid = True
- L43: self.scan_profile_valid = False
- L70: def record_scan_start(self, mode: str, output_file: str) -> None:
- L71: self.last_scan_mode = mode
- L73: self.acquisition_status = "scan running"
- L75: def record_scan_output(self, output_file: str, plot_file: str, point_count: int) -> None:
- L79: self.acquisition_status = f"{point_count} raster points loaded"
- L90: validation = "VALID" if self.scan_profile_valid else "NOT VALIDATED"

### `core\education\config_loader.py`

- L34: def get_scan_mode_presets(config):
- L35: """Extract scan-mode hardware and timing presets."""
- L36: return config.get("scan_mode_presets", {})
- L39: def get_scan_mode_preset(config, mode):
- L40: """Return the preset for a scan mode, or fall back to the default scan area."""
- L41: presets = get_scan_mode_presets(config)
- L46: "description": "Default scan profile from project configuration.",
- L47: "scan_area": config["scan_area"],
- L51: "approach_start": config["scan_area"]["z"],
- L52: "approach_target": config["scan_area"]["z"],
- L53: "retract_target": config["scan_area"]["z"],
- L67: def get_safe_raster_config(config):

### `core\education\safe_raster.py`

- L8: scan_direction: str
- L31: """Generate raster points row by row."""
- L37: def generate_grid_from_scan_area(scan_area):
- L38: """Generate raster points from scan-area min/max/resolution settings."""
- L40: scan_area["x_min"],
- L41: scan_area["x_max"],
- L42: scan_area["x_resolution"],
- L45: scan_area["y_min"],
- L46: scan_area["y_max"],
- L47: scan_area["y_resolution"],
- L53: def generate_bidirectional_grid_from_scan_area(scan_area):
- L54: """Generate forward/backward and upward/downward raster passes."""

### `core\education\scan_profile.py`

- L39: def validate_scan_profile(profile: ScanProfile, limits: MotionLimits) -> None:
- L41: raise ValueError(f"Invalid scan mode: {profile.mode}")

### `core\education\synthetic_signal.py`

- L13: It is a safe teaching signal for raster-scan visualization.

### `core\hardware\hardware_command_log.py`

- L16: with path.open("a", encoding="utf-8", newline="") as file:

### `core\motion\prusa_gcode_backend.py`

- L83: def _parse_m114(self, lines: List[str]) -> Dict[str, float]:
- L85: Parse M114 response lines into position dict.
- L88: joined = " ".join(lines)
- L110: """Collect lines until 'ok' or timeout."""
- L115: raw = self._ser.readline()
- L128: Send a single G-code command and return the response lines (until ok/timeout).
- L132: line = cmd.strip()
- L133: if not line:
- L135: self._ser.write((line + "\n").encode("ascii", errors="ignore"))
- L183: lines = self.send_gcode("M114", timeout=2.5)
- L184: parsed = self._parse_m114(lines)
- L206: lines = self.send_gcode("M114", timeout=3.0)

### `core\scan\base_scan_mode.py`

- L1: # core/scan/base_scan_mode.py
- L8: Abstract base class for all scan modes (STM, AFM-Contact, AFM-NonContact, Profiling).
- L31: Return the accumulated scan data buffer.
- L37: Apply new scan configuration at runtime.

### `core\scan\__init__.py`

- L6: base_scan_mode,

### `core\scan\controller\scan_manager.py`

- L1: # control/scan_manager.py
- L7: def __init__(self, scan_mode_instance, use_simulation=True):
- L10: scan_mode_instance (BaseScanMode): Instance of the selected scan mode.
- L13: self.scan_mode = scan_mode_instance
- L16: self._scan_thread = None
- L20: def start_scan(self):
- L21: if self._scan_thread and self._scan_thread.is_alive():
- L27: self._scan_thread = threading.Thread(target=self._run_scan_loop, daemon=True)
- L28: self._scan_thread.start()
- L31: def _run_scan_loop(self):
- L37: result = self.scan_mode.perform_step()
- L42: def pause_scan(self):

### `core\scan\modes\afm_contact_mode.py`

- L1: # core/scan/afm_contact_mode.py
- L5: from core.scan.base_scan_mode import BaseScanMode
- L13: Implements AFM Contact Mode scan behavior.
- L53: print("[AFMContactMode] Finalizing scan...")
- L68: def run_contact_scan():
- L69: print('Stub function run_contact_scan called.')

### `core\scan\modes\afm_noncontact_mode.py`

- L5: from .base_scan_mode import BaseScanMode
- L57: print("[AFMNonContactMode] Finalizing scan...")
- L76: def run_noncontact_scan():
- L77: print('Stub function run_noncontact_scan called.')

### `core\scan\modes\base_scan_mode.py`

- L1: # core/scan/stm_mode.py
- L5: from core.scan.base_scan_mode import BaseScanMode
- L7: from core.scan.modes import stm_mode

### `core\scan\modes\profiling_mode.py`

- L1: # core/scan/profiling_mode.py
- L5: from core.scan.base_scan_mode import BaseScanMode
- L11: Profiling mode for 1D surface scanning along a single axis (X or Y),
- L55: print("[ProfilingMode] Finalizing scan...")
- L68: # D:/Documents/Project/SPM/core/scan/profiling_mode.py

## web_api

### `core\ai\academic_ai_client.py`

- L28: api_key = os.getenv("ACADEMIC_AI_API_KEY", "").strip()
- L31: configured = bool(base_url and api_key and model_or_assistant)

### `core\web\operator_console_server.py`

- L14: from core.web.system_control import dry_run_startup_plan, system_close, system_off, system_on, system_status
- L18: WEB_ROOT = PROJECT_ROOT / "web" / "operator_console"
- L87: if route == "/api/system/status":
- L91: if route == "/api/system/on":
- L96: if route == "/api/system/off":
- L100: if route == "/api/system/close":
- L104: if route == "/api/system/dry-run":
- L108: if route == "/api/status":
- L112: "console": "web_operator_console",
- L134: if route == "/api/phase-map":
- L138: if route == "/api/ai/status":
- L150: if route == "/api/ai/recommendation":

### `docs\PHASE1_CODE_MAP.md`

- L902: - docs\versions\v0.20.0_ht3_4_smart_operator_console_2026-06-12\TWO_LAYER_SPM_DEVELOPMENT_ROADMAP_2026-06-12.md:263: - Added connection status display.
- L903: - docs\versions\v0.20.0_ht3_4_smart_operator_console_2026-06-12\TWO_LAYER_SPM_DEVELOPMENT_ROADMAP_2026-06-12.md:264: - Added live XYZ position status display.

### `docs\PHASE_1_8F_DIRTY_TREE_CLASSIFICATION_2026-06-16.md`

- L114: UNTRACKED        GENERATED_DATA_REVIEW_LATER data/v0.20.0_smart_operator_console.png

### `docs\PHASE_1_8G_PROFESSIONAL_STABLE_CHECKPOINT_2026-06-16.md`

- L125: data/v0.20.0_smart_operator_console.png
- L204: docs/versions/v0.20.0_ht3_4_smart_operator_console_2026-06-12/README.md
- L205: docs/versions/v0.20.0_ht3_4_smart_operator_console_2026-06-12/TWO_LAYER_SPM_DEVELOPMENT_ROADMAP_2026-06-12.md
- L206: docs/versions/v0.20.0_ht3_4_smart_operator_console_2026-06-12/hardware_test_console_gui.py
- L207: docs/versions/v0.20.0_ht3_4_smart_operator_console_2026-06-12/smart_hardware_assessment.py
- L208: docs/versions/v0.20.0_ht3_4_smart_operator_console_2026-06-12/test_hardware_test_console_gui.py
- L209: docs/versions/v0.20.0_ht3_4_smart_operator_console_2026-06-12/test_smart_hardware_assessment.py

### `docs\PHASE_2_0_WEB_OPERATOR_CONSOLE.md`

- L76: - `/api/status`
- L77: - `/api/phase-map`

### `docs\PHASE_2_1E_MAIN_SYSTEM_DRY_RUN.md`

- L11: - `/api/system/status`
- L12: - `/api/system/on?mode=dry_run`
- L13: - `/api/system/off`
- L14: - `/api/system/close`
- L15: - `/api/system/dry-run`
- L67: - connect `/api/system/status` to real read-only status if available

### `docs\PHASE_2_2_ACADEMIC_AI_ADVISORY_LAYER.md`

- L41: - `/api/ai/status`
- L42: - `/api/ai/recommendation?task=approach`
- L43: - `/api/ai/recommendation?task=scan`
- L44: - `/api/ai/recommendation?task=simulation`
- L45: - `/api/ai/recommendation?task=diagnosis`

### `docs\PHASE_2_3_SPM_RASTER_SCAN_MODEL.md`

- L42: - `/api/scan/profile`
- L43: - `/api/scan/line`

### `docs\versions\v0.10.0_matrix_workspace_phase1_2026-06-11\backup\test_gui_z_dry_run_safety.py`

- L427: def test_gui_uses_two_row_operator_console_for_monitor_fit():

### `docs\versions\v0.10.1_clear_workstation_windows_2026-06-11\backup\test_gui_z_dry_run_safety.py`

- L427: def test_gui_uses_two_row_operator_console_for_monitor_fit():

### `docs\versions\v0.11.0_live_spm_raster_measurement_2026-06-11\backup\test_gui_z_dry_run_safety.py`

- L427: def test_gui_uses_two_row_operator_console_for_monitor_fit():

### `docs\versions\v0.11.1_crash_hardened_live_measurement_2026-06-11\backup\test_gui_z_dry_run_safety.py`

- L427: def test_gui_uses_two_row_operator_console_for_monitor_fit():

### `docs\versions\v0.11.2_text_live_scan_stability_2026-06-11\backup\test_gui_z_dry_run_safety.py`

- L427: def test_gui_uses_two_row_operator_console_for_monitor_fit():

### `docs\versions\v0.21.0_main_initialize_and_z_scanner_workflow_2026-06-12\test_gui_z_dry_run_safety.py`

- L433: def test_gui_uses_two_row_operator_console_for_monitor_fit():

### `docs\versions\v0.22.0_essential_initialize_and_mk4s_z_auto_approach_2026-06-12\test_gui_z_dry_run_safety.py`

- L433: def test_gui_uses_two_row_operator_console_for_monitor_fit():

### `docs\versions\v0.23.0_single_z_scanner_gwyddion_cleanup_2026-06-12\test_gui_z_dry_run_safety.py`

- L433: def test_gui_uses_two_row_operator_console_for_monitor_fit():

### `docs\versions\v0.24.0_connect_approach_measurement_main_page_2026-06-12\test_gui_z_dry_run_safety.py`

- L433: def test_gui_uses_two_row_operator_console_for_monitor_fit():

### `docs\versions\v0.25.0_focused_main_workflow_cleanup_2026-06-15\test_gui_z_dry_run_safety.py`

- L433: def test_gui_uses_two_row_operator_console_for_monitor_fit():

### `tests\test_gui_z_dry_run_safety.py`

- L433: def test_gui_uses_two_row_operator_console_for_monitor_fit():

### `tests\test_web_operator_console.py`

- L3: from core.web.operator_console_server import PHASE_MAP, WEB_ROOT, json_response
- L9: def test_web_operator_console_files_exist():
- L28: def test_json_response_serializes_api_payload():
- L36: def test_web_operator_console_main_page_is_not_roadmap_page():
- L44: def test_web_operator_console_has_dropdown_menus():
- L63: def test_web_operator_console_uses_non_blocking_windows():
- L76: def test_web_operator_console_main_page_keeps_essential_controls():
- L108: def test_web_operator_console_has_directional_line_and_topography_windows():
- L128: def test_web_operator_console_has_academic_ai_window():
- L135: assert "/api/ai/status" in app_js
- L136: assert "/api/ai/recommendation" in app_js
- L139: def test_web_operator_console_uses_modular_raster_js():

### `tools\generate_clean_tests.py`

- L37: class_name = "Test" + ''.join(word.capitalize() for word in module_name.split('_'))

### `tools\launch_web_operator_console.ps1`

- L31: -ArgumentList "tools\run_web_operator_console.py --host 127.0.0.1 --port $Port" `
- L45: $response = Invoke-WebRequest -Uri "$url/api/status" -UseBasicParsing -TimeoutSec 2

### `tools\phase_2_1f_discover_hardware_modules.py`

- L28: "web_api": ["api", "operator_console", "system_control"],

### `tools\run_web_operator_console.py`

- L18: from core.web.operator_console_server import main  # noqa: E402

## Recommended next integration target

Use this report to choose the safest existing module for:

1. read-only printer status,
2. dry-run startup plan,
3. explicit hardware lockout,
4. later real read-only serial status,
5. only after that: controlled motion through safety gates.
