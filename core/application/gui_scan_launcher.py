from __future__ import annotations

import subprocess
import sys
from pathlib import Path

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
)

from core.education.config_loader import load_config, get_safe_feedrates
from core.education.scan_profile import (
    ScanProfile,
    MotionLimits,
    validate_scan_profile,
)

from core.z_control.z_driver_arduino_safe import ZDriverArduino


# ============================================================
# SPM Educational GUI
# Safe GUI wrapper around the verified CLI scan launcher
# ============================================================
class ScanGUI(QWidget):
    # ------------------------------------------------------------
    # GUI constructor
    # ------------------------------------------------------------
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SPM Educational Interface - Safe Mode")

        # ------------------------------------------------------------
        # Load configuration
        # ------------------------------------------------------------
        self.config = load_config()
        self.safe_feedrates = get_safe_feedrates(self.config)

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

        # ------------------------------------------------------------
        # Output CSV path
        # ------------------------------------------------------------
        self.output_file = QLineEdit("data/interface_test_output.csv")

        form_layout.addRow("X min:", self.x_min)
        form_layout.addRow("X max:", self.x_max)
        form_layout.addRow("Y min:", self.y_min)
        form_layout.addRow("Y max:", self.y_max)
        form_layout.addRow("Z:", self.z)
        form_layout.addRow("X resolution:", self.x_res)
        form_layout.addRow("Y resolution:", self.y_res)
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
        form_layout.addRow("Plot color map:", self.color_map_dropdown)

        # ------------------------------------------------------------
        # Buttons
        # ------------------------------------------------------------
        self.validate_btn = QPushButton("Validate Profile")
        self.validate_btn.clicked.connect(self.validate_profile)

        self.dry_run_btn = QPushButton("Dry Run Scan - No Hardware Movement")
        self.dry_run_btn.clicked.connect(self.run_dry_scan)

        self.execute_btn = QPushButton("Execute Hardware Scan")
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

        self.z_move_test_btn = QPushButton("Z Dry Run: Move Z Test")
        self.z_move_test_btn.clicked.connect(self.run_z_dry_move_test)

        self.z_approach_btn = QPushButton("Z Dry Run: Approach")
        self.z_approach_btn.clicked.connect(self.run_z_dry_approach)

        self.z_retract_btn = QPushButton("Z Dry Run: Retract")
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

        main_layout.addLayout(form_layout)
        main_layout.addWidget(self.validate_btn)
        main_layout.addWidget(self.dry_run_btn)
        main_layout.addWidget(self.execute_btn)
        z_group = QGroupBox("Z-control dry-run tools")
        z_layout = QVBoxLayout()

        z_connection_group = QGroupBox("Z Connection")
        z_connection_layout = QVBoxLayout()

        z_connection_bar = QHBoxLayout()
        z_connection_bar.addWidget(self.z_connection_state_label)
        z_connection_bar.addWidget(self.z_connect_btn)
        z_connection_bar.addWidget(self.z_disconnect_btn)

        z_connection_layout.addLayout(z_connection_bar)
        z_connection_layout.addWidget(self.z_status_label)
        z_connection_group.setLayout(z_connection_layout)

        z_move_group = QGroupBox("Z Move Test")
        z_move_layout = QVBoxLayout()
        z_move_layout.addWidget(QLabel("Z dry-run test position:"))
        z_move_layout.addWidget(self.z_test_position)
        z_move_layout.addWidget(self.z_move_test_btn)
        z_move_group.setLayout(z_move_layout)

        z_approach_group = QGroupBox("Z Approach")
        z_approach_layout = QVBoxLayout()
        z_approach_layout.addWidget(QLabel("Approach start Z:"))
        z_approach_layout.addWidget(self.z_approach_start)
        z_approach_layout.addWidget(QLabel("Approach target Z:"))
        z_approach_layout.addWidget(self.z_approach_target)
        z_approach_layout.addWidget(QLabel("Z dry-run step size:"))
        z_approach_layout.addWidget(self.z_step_size)
        z_approach_layout.addWidget(self.z_approach_btn)
        z_approach_group.setLayout(z_approach_layout)

        z_retract_group = QGroupBox("Z Retract")
        z_retract_layout = QVBoxLayout()
        z_retract_layout.addWidget(QLabel("Retract start Z:"))
        z_retract_layout.addWidget(self.z_retract_start)
        z_retract_layout.addWidget(QLabel("Retract target Z:"))
        z_retract_layout.addWidget(self.z_retract_target)
        z_retract_layout.addWidget(self.z_retract_btn)
        z_retract_group.setLayout(z_retract_layout)

        z_layout.addWidget(z_connection_group)
        z_layout.addWidget(z_move_group)
        z_layout.addWidget(z_approach_group)
        z_layout.addWidget(z_retract_group)
        z_group.setLayout(z_layout)

        main_layout.addWidget(z_group)
        main_layout.addWidget(QLabel("Status log:"))
        main_layout.addWidget(self.log)

        self.setLayout(main_layout)
        self.resize(620, 520)

    # ------------------------------------------------------------
    # Select output CSV file
    # ------------------------------------------------------------
    def select_output_file(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Select Output CSV",
            "",
            "CSV Files (*.csv)",
        )

        if path:
            self.output_file.setText(path)
            self.append_log(f"Output CSV selected: {path}")

    # ------------------------------------------------------------
    # Update selected color map
    # ------------------------------------------------------------
    def update_color_map(self, color_map: str) -> None:
        self.color_map = color_map
        self.append_log(f"Plot color map selected: {self.color_map}")

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
        self.append_log(f"[Z STATUS] {label_text}")

    def report_z_failure(self, status_text: str, log_text: str) -> None:
        label_text = f"Z dry-run status: {status_text}"
        self.z_status_label.setText(label_text)
        self.append_log(f"[Z FAILURE] {log_text}")

    # ------------------------------------------------------------
    # Z-control dry-run: connect
    # No real hardware movement
    # ------------------------------------------------------------
    def run_z_dry_connect(self) -> None:
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
        self.append_log(f"[Z DRY RUN] Move Z test to {z_position}: PASS")

    # ------------------------------------------------------------
    # Z-control dry-run: approach
    # No real hardware movement
    # ------------------------------------------------------------
    def run_z_dry_approach(self) -> None:
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
        self.append_log(
            f"[Z DRY RUN] Approach from {start_z} to {target_z} with step {step_size}: PASS"
        )

    # ------------------------------------------------------------
    # Z-control dry-run: retract
    # No real hardware movement
    # ------------------------------------------------------------
    def run_z_dry_retract(self) -> None:
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
        self.append_log(
            f"[Z DRY RUN] Retract from {start_z} to {target_z} with step {step_size}: PASS"
        )

    # ------------------------------------------------------------
    # Z-control dry-run: disconnect
    # No real hardware movement
    # ------------------------------------------------------------
    def run_z_dry_disconnect(self) -> None:
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
            feedrate_xy=self.safe_feedrates["xy"],
            feedrate_z=self.safe_feedrates["z"],
            mode="SIMULATED_SURFACE",
        )

    # ------------------------------------------------------------
    # Validate profile against locked motion limits
    # ------------------------------------------------------------
    def validate_profile(self) -> ScanProfile | None:
        try:
            profile = self.build_profile()
            validate_scan_profile(profile, self.limits)

            self.append_log("Validation: PASS")
            self.append_log(str(profile))
            self.append_log(f"Selected color map: {self.color_map}")

            QMessageBox.information(
                self,
                "Validation",
                "Scan profile VALID.",
            )

            return profile

        except Exception as error:
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

    # ------------------------------------------------------------
    # Dry-run scan
    # ------------------------------------------------------------
    def run_dry_scan(self) -> None:
        profile = self.validate_profile()

        if profile is None:
            self.append_log("Dry run cancelled because validation failed.")
            return

        confirmation_message = self.build_scan_confirmation_message(
            profile,
            execute_hardware=False,
        )

        if not self.confirm_critical_action("Confirm dry-run scan", confirmation_message):
            self.append_log("[SCAN] Dry-run scan cancelled by operator")
            return

        self.append_log(f"Dry run using color map: {self.color_map}")

        command = self.build_cli_command(profile, execute_hardware=False)
        exit_code = self.run_command(command, "scan")

        if exit_code == 0:
            plot_exit_code, plot_path = self.generate_plot()

            if plot_exit_code == 0:
                self.append_log(f"Dry run plot generated: {plot_path}")
                QMessageBox.information(
                    self,
                    "Dry Run",
                    (
                        "Dry run completed successfully.\n\n"
                        "No hardware movement was performed.\n\n"
                        f"Plot saved to:\n{plot_path}"
                    ),
                )
            else:
                self.append_log(f"Plot generation failed with exit code {plot_exit_code}")
                QMessageBox.warning(
                    self,
                    "Dry Run",
                    (
                        "Dry run completed successfully, but plot generation failed.\n\n"
                        "Check the status log for details."
                    ),
                )
        else:
            self.append_log(f"Dry run failed with exit code {exit_code}")
            QMessageBox.critical(
                self,
                "Dry Run",
                f"Dry run failed with exit code {exit_code}",
            )

    # ------------------------------------------------------------
    # Hardware scan
    # ------------------------------------------------------------
    def run_hardware_scan(self) -> None:
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

        command = self.build_cli_command(profile, execute_hardware=True)
        exit_code = self.run_command(command, "scan")

        if exit_code == 0:
            plot_exit_code, plot_path = self.generate_plot()

            if plot_exit_code == 0:
                self.append_log(f"Hardware scan plot generated: {plot_path}")
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


# ------------------------------------------------------------
# Program entry point
# ------------------------------------------------------------
    def closeEvent(self, event) -> None:
        if self.z_driver.connected:
            message = (
                "The Z dry-run controller is still connected.\n\n"
                "Close the SPM workstation GUI anyway?\n\n"
                "Recommended action: disconnect Z before closing."
            )
        else:
            message = (
                "Close the SPM workstation GUI?\n\n"
                "Any unsaved scan settings or log information may be lost."
            )

        if self.confirm_critical_action("Confirm GUI close", message):
            self.append_log("[GUI] Close confirmed by operator")
            event.accept()
        else:
            self.append_log("[GUI] Close cancelled by operator")
            event.ignore()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = ScanGUI()
    gui.show()
    sys.exit(app.exec_())








