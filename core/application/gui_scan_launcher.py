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
    QVBoxLayout,
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
        # Status log
        # ------------------------------------------------------------
        self.log = QTextEdit()
        self.log.setReadOnly(True)

        main_layout.addLayout(form_layout)
        main_layout.addWidget(self.validate_btn)
        main_layout.addWidget(self.dry_run_btn)
        main_layout.addWidget(self.execute_btn)
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

        reply = QMessageBox.question(
            self,
            "Confirm Hardware Movement",
            (
                "This will move the Prusa MK4S hardware.\n\n"
                "Confirm that the bed, nozzle, and probe area are clear.\n\n"
                f"Scan profile:\n{profile}\n\n"
                f"Output file:\n{self.output_file.text()}\n\n"
                f"Selected color map:\n{self.color_map}\n\n"
                "Continue?"
            ),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply != QMessageBox.Yes:
            self.append_log("Hardware scan cancelled by user.")
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
if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = ScanGUI()
    gui.show()
    sys.exit(app.exec_())
