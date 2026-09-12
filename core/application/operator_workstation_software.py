from __future__ import annotations

import contextlib
import io
import json
import os
import subprocess
import sys
import math
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

if "MPLCONFIGDIR" not in os.environ:
    os.environ["MPLCONFIGDIR"] = os.path.join(tempfile.gettempdir(), "matplotlib_spm")
os.environ.setdefault("SPM_WEB_ALLOW_READONLY_HARDWARE", "1")

from PyQt6.QtCore import QSettings, QThread, QTimer, Qt, pyqtSignal
from PyQt6.QtGui import QAction, QColor, QPainter, QPen
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QButtonGroup,
    QCheckBox,
    QDialog,
    QDoubleSpinBox,
    QFileDialog,
    QFrame,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressDialog,
    QProgressBar,
    QPushButton,
    QRadioButton,
    QSpinBox,
    QSplitter,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from core.system.mk4s_z_auto_approach import run_mk4s_z_move_to_setpoint
from core.ai.academic_ai_client import build_ai_recommendation
from core.ai.autonomous_spm_agent import AutonomousSPMAgent
from core.ai.academic_gcode_generator import GCodePatternRequest, build_academic_gcode_job, build_gcode_plan
from core.ai.spm_approach_advisor import ApproachAdvisorInput, advise_approach
from core.z_control.crtouch_probe_plan import CRTouchProbePlan
from core.web.system_control import (
    system_calibration,
    system_calibration_repeatability,
    system_diagnostics,
    system_disconnect,
    system_health_test,
    system_safe_standby,
    system_safe_standby_for_close,
)
from core.web.z_scanner_control import z_auto_approach, z_read_status, z_reference_payload, z_retract, z_stop_now
from core.web.spm_scan_simulation import WebScanProfile, raster_line_coordinates
from core.web.real_scan_control import (
    clear_real_scan_pause,
    FoilTapConfig,
    request_real_scan_pause,
    request_real_scan_stop,
    run_real_foil_tap_scan,
    run_real_constant_z_scan,
)
from core.web.mk4s_motion_limits import motion_limits_payload
from core.application.scan_constraints import load_scan_constraints, validate_scan_rectangle
from core.application.modules.connection_manager import ConnectionManager, discover_ports
from core.application.modules.console_logger import ConsoleLogger
from core.application.modules.simulation import SampleGenerator, SimulationEngine
from core.application.modules.dry_run import run_hardware_dry_run
from core.application.version import BUILD_DATE_DISPLAY, FULL_VERSION, VERSION_STRING, git_build_id
from core.hardware.mega_probe import (
    MegaProbeSerialTransport,
    discover_mega_candidate_ports,
)
from core.hardware.spm_system import discover_spm_ports, evaluate_spm_readiness
from core.hardware.crtouch_mount_profile import (
    load_mount_profiles,
    mount_profile_blockers,
)
from core.hardware.stage2_scanner_profile import stage2_thermal_blockers
from core.web.mk4s_readonly_connection import connect_real_hardware_readonly
from tools.run_verified_two_magnet_map import (
    RESOLUTION_PROFILES as TWO_MAGNET_RESOLUTION_PROFILES,
    run as run_verified_two_magnet_map,
)


APP_VERSION = VERSION_STRING
APP_TITLE = f"SPM Operator — {FULL_VERSION} ({BUILD_DATE_DISPLAY}) | Phase 2.1 Teaching Edition"
Z_VIEW_FULL_RANGE = (0.0, 220.0)
SYSTEM_CONTROL_WINDOW_WIDTH = 1180
SYSTEM_CONTROL_WINDOW_HEIGHT = 820
# Professional scientific instrument palette — Bruker/Park/Oxford style
# Primary action (connect, start scan)
GREEN_BUTTON_STYLE = (
    "QPushButton { background: #16A34A; color: white; font-weight: 700; padding: 8px; border-radius: 4px; }"
    "QPushButton:hover { background: #15803D; }"
    "QPushButton:disabled { background: #D1D5DB; color: #9CA3AF; }"
)
# Destructive action (E-stop, disconnect)
RED_BUTTON_STYLE = (
    "QPushButton { background: #DC2626; color: white; font-weight: 700; padding: 8px; border-radius: 4px; }"
    "QPushButton:hover { background: #B91C1C; }"
    "QPushButton:disabled { background: #D1D5DB; color: #9CA3AF; }"
)
# Connect / pending action (amber → blue in professional palette)
YELLOW_BUTTON_STYLE = (
    "QPushButton { background: #2563EB; color: white; font-weight: 700; padding: 8px; border-radius: 4px; }"
    "QPushButton:hover { background: #1D4ED8; }"
    "QPushButton:disabled { background: #D1D5DB; color: #9CA3AF; }"
)
# Disabled / greyed-out action
DISABLED_BUTTON_STYLE = (
    "QPushButton { background: #E5E7EB; color: #9CA3AF; font-weight: 700; padding: 8px; border-radius: 4px; }"
)
# Secondary / service action (ghost)
GRAY_BUTTON_STYLE = (
    "QPushButton { background: #F3F4F6; color: #374151; font-weight: 600; padding: 8px;"
    "border: 1px solid #D1D5DB; border-radius: 4px; }"
    "QPushButton:hover { background: #E5E7EB; }"
    "QPushButton:disabled { background: #F9FAFB; color: #9CA3AF; }"
)
LINE_VIEW_LABELS = ("Line Mode X+", "Line Mode X-", "Line Mode Y+", "Line Mode Y-")
TOPOGRAPHY_VIEW_LABELS = ("Topography X+", "Topography X-", "Topography Y+", "Topography Y-")


class ZTraceWidget(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.samples: list[float] = []
        self.view_mode = "auto"
        self.zoom_window_mm = 2.0
        self.setMinimumHeight(220)

    def add_sample(self, z_value: float) -> None:
        self.samples.append(float(z_value))
        self.samples = self.samples[-400:]
        self.update()

    def set_view_mode(self, mode: str) -> None:
        self.view_mode = mode
        self.update()

    def set_zoom_window(self, value: float) -> None:
        self.zoom_window_mm = max(0.01, float(value))
        self.update()

    def clear(self) -> None:
        self.samples.clear()
        self.update()

    def paintEvent(self, _event: Any) -> None:  # noqa: N802
        painter = QPainter(self)
        # Professional light background — instrument oscilloscope style
        painter.fillRect(self.rect(), QColor("#FAFBFC"))
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        width = self.width()
        height = self.height()
        margin_left = 48
        margin_right = 14
        margin_top = 26
        margin_bottom = 30
        plot_w = max(1, width - margin_left - margin_right)
        plot_h = max(1, height - margin_top - margin_bottom)

        # Subtle grid lines
        painter.setPen(QPen(QColor("#E5E7EB"), 1))
        for i in range(6):
            y = margin_top + (plot_h * i / 5)
            painter.drawLine(margin_left, int(y), width - margin_right, int(y))

        painter.setPen(QColor("#6B7280"))
        painter.drawText(12, 18, f"Live Z signal ({self.view_mode})")
        painter.drawText(8, margin_top + 12, "Z mm")

        if not self.samples:
            painter.drawText(margin_left, margin_top + 34, "Read Z or apply a target to start the trace")
            return

        latest = self.samples[-1]
        low = min(self.samples)
        high = max(self.samples)
        if self.view_mode == "full":
            low, high = Z_VIEW_FULL_RANGE
        elif self.view_mode == "zoom":
            half = self.zoom_window_mm / 2.0
            low, high = latest - half, latest + half
        else:
            pad = max((high - low) * 0.18, 0.05)
            low, high = low - pad, high + pad
        span = max(0.01, high - low)

        # Professional blue signal trace
        painter.setPen(QPen(QColor("#2563EB"), 2))
        points = self.samples[-240:]
        last_x = last_y = None
        for index, value in enumerate(points):
            x = margin_left + int((index / max(1, len(points) - 1)) * plot_w)
            normalized = max(0.0, min(1.0, (value - low) / span))
            y = margin_top + plot_h - int(normalized * plot_h)
            if last_x is not None and last_y is not None:
                painter.drawLine(last_x, last_y, x, y)
            last_x, last_y = x, y

        painter.setPen(QColor("#374151"))
        painter.drawText(12, height - 10, f"view {low:.3f}..{high:.3f} mm | current {latest:.3f} mm")
        painter.drawText(12, margin_top + 2, f"{high:.2f}")
        painter.drawText(12, margin_top + plot_h, f"{low:.2f}")


class SignalPlotWidget(QWidget):
    def __init__(self, title: str, mode: str, direction: str) -> None:
        super().__init__()
        self.title = title
        self.mode = mode
        self.direction = direction
        self.lines: list[list[dict[str, float]]] = []
        self.current_line: list[dict[str, float]] = []
        self.setMinimumSize(640, 360)

    def set_scan_data(self, lines: list[list[dict[str, float]]], current_line: list[dict[str, float]]) -> None:
        self.lines = [list(line) for line in lines]
        self.current_line = list(current_line)
        self.update()

    def paintEvent(self, _event: Any) -> None:  # noqa: N802
        painter = QPainter(self)
        # Professional light background
        painter.fillRect(self.rect(), QColor("#FAFBFC"))
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QColor("#1A1F2B"))
        painter.drawText(14, 22, self.title)

        if self.mode == "line":
            self.paint_line(painter)
        else:
            self.paint_topography(painter)

    def selected_line(self) -> list[dict[str, float]]:
        line = self.current_line or (self.lines[-1] if self.lines else [])
        if self.direction.endswith("-"):
            return list(reversed(line))
        return line

    def paint_line(self, painter: QPainter) -> None:
        line = self.selected_line()
        if not line:
            painter.setPen(QColor("#6B7280"))
            painter.drawText(24, 58, "Line mode waiting for measurement points")
            return

        values = [float(point["z_feedback"]) for point in line]
        low = min(values)
        high = max(values)
        flat_signal = abs(high - low) < 1e-9
        if flat_signal:
            low -= 0.05
            high += 0.05
        span = max(1e-9, high - low)
        left, top, right, bottom = 54, 42, 18, 34
        width = max(1, self.width() - left - right)
        height = max(1, self.height() - top - bottom)

        # Subtle grid lines
        painter.setPen(QPen(QColor("#E5E7EB"), 1))
        for i in range(5):
            y = top + int(height * i / 4)
            painter.drawLine(left, y, self.width() - right, y)

        # Professional blue signal trace
        painter.setPen(QPen(QColor("#2563EB"), 2))
        last_x = last_y = None
        point_pixels: list[tuple[int, int]] = []
        for index, value in enumerate(values):
            x = left + int(index / max(1, len(values) - 1) * width)
            y = top + height - int(((value - low) / span) * height)
            if last_x is not None:
                painter.drawLine(last_x, last_y, x, y)
            last_x, last_y = x, y
            point_pixels.append((x, y))

        painter.setPen(QPen(QColor("#93C5FD"), 1))
        painter.setBrush(QColor("#2563EB"))
        for x, y in point_pixels:
            painter.drawEllipse(x - 3, y - 3, 6, 6)
        if point_pixels:
            x, y = point_pixels[-1]
            painter.setBrush(QColor("#ffffff"))
            painter.drawEllipse(x - 5, y - 5, 10, 10)

        painter.setPen(QColor("#374151"))
        latest_source = str(line[-1].get("feedback_source", "z_feedback"))
        painter.drawText(12, top + 4, f"{high:.3f} mm")
        painter.drawText(12, top + height, f"{low:.3f} mm")
        painter.drawText(left, self.height() - 10, f"{len(values)} points | latest {values[-1]:.4f} mm | {latest_source}")

    def paint_topography(self, painter: QPainter) -> None:
        rows = list(self.lines)
        if self.current_line:
            rows.append(list(self.current_line))
        if not rows:
            painter.setPen(QColor("#6B7280"))
            painter.drawText(24, 58, "Topography waiting for accumulated scan lines")
            return

        if self.direction.startswith("Y-"):
            rows = list(reversed(rows))
        all_values = [float(point["z_feedback"]) for row in rows for point in row]
        low = min(all_values)
        high = max(all_values)
        flat_signal = abs(high - low) < 1e-9
        span = max(1e-9, high - low)
        left, top, right, bottom = 20, 42, 18, 24
        width = max(1, self.width() - left - right)
        height = max(1, self.height() - top - bottom)
        cell_h = max(1, height / max(1, len(rows)))

        for row_index, row in enumerate(rows):
            points = list(row)
            if self.direction.startswith("X-"):
                points = list(reversed(points))
            cell_w = max(1, width / max(1, len(points)))
            for col, point in enumerate(points):
                value = float(point["z_feedback"])
                normalized = 0.55 if flat_signal else (value - low) / span
                color = QColor.fromHsvF(0.62 - 0.62 * normalized, 0.88, 0.30 + 0.62 * normalized)
                cell_x = int(left + col * cell_w)
                cell_y = int(top + row_index * cell_h)
                cell_width = max(1, math.ceil(cell_w))
                cell_height = max(1, math.ceil(cell_h))
                painter.fillRect(
                    cell_x,
                    cell_y,
                    cell_width,
                    cell_height,
                    color,
                )
                painter.setPen(QPen(QColor("#E5E7EB"), 1))
                painter.drawRect(cell_x, cell_y, cell_width, cell_height)

        painter.setPen(QColor("#374151"))
        painter.drawText(left, self.height() - 8, f"{len(rows)} lines | Z {low:.4f}..{high:.4f} mm")


class ToolWindow(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.WindowMinMaxButtonsHint
            | Qt.WindowType.WindowCloseButtonHint
        )

    def closeEvent(self, event: Any) -> None:  # noqa: N802
        event.ignore()
        self.hide()


class SimulationConfigDialog(QDialog):
    """Live virtual-sample configuration and topography preview."""

    PARAMETER_LABELS = {
        "radius": "Radius (mm)", "width": "Width (mm)", "height": "Height (mm)",
        "edge_sharpness": "Edge softness (mm)", "lattice_constant": "Lattice constant (mm)",
        "lattice_constant_a": "Lattice A (mm)", "lattice_constant_b": "Lattice B (mm)",
        "rotation": "Rotation (deg)", "center_x": "Center X (mm)", "center_y": "Center Y (mm)",
    }

    def __init__(self, owner: "OperatorWorkstation") -> None:
        super().__init__(owner)
        self.owner = owner
        self.setWindowTitle("Virtual Sample Configuration")
        self.resize(760, 640)
        layout = QVBoxLayout(self)
        self.sample_select = QComboBox()
        self.sample_select.addItems([owner.simulation_sample_label(name) for name in SampleGenerator.SAMPLE_TYPES])
        self.sample_select.setCurrentText(owner.simulation_sample_label(owner.simulation_sample_type))
        self.sample_select.currentTextChanged.connect(self.load_sample)
        layout.addWidget(QLabel("Virtual Sample"))
        layout.addWidget(self.sample_select)
        self.preview = SignalPlotWidget("Virtual Sample Topography", "topography", "X+")
        self.preview.setMinimumHeight(260)
        layout.addWidget(self.preview, 1)
        self.form = QFormLayout()
        self.fields: dict[str, QDoubleSpinBox] = {}
        for key, label in self.PARAMETER_LABELS.items():
            field = QDoubleSpinBox()
            field.setRange(-1000.0 if key.startswith("center_") or key == "rotation" else 0.001, 1000.0)
            field.setDecimals(4)
            field.valueChanged.connect(self.refresh_preview)
            self.fields[key] = field
            self.form.addRow(label, field)
        layout.addLayout(self.form)
        buttons = QHBoxLayout()
        apply_button = QPushButton("Apply")
        apply_button.setStyleSheet(GREEN_BUTTON_STYLE)
        apply_button.clicked.connect(self.apply)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        buttons.addStretch(1)
        buttons.addWidget(apply_button)
        buttons.addWidget(cancel_button)
        layout.addLayout(buttons)
        self.load_sample(self.sample_select.currentText())

    def load_sample(self, label: str) -> None:
        sample_type = self.owner.simulation_sample_key(label)
        params = self.owner.simulation_defaults(sample_type)
        active_keys = self.owner.simulation_parameter_keys(sample_type)
        for key, field in self.fields.items():
            field.blockSignals(True)
            field.setValue(float(params.get(key, 0.0)))
            visible = key in active_keys
            field.setVisible(visible)
            label_widget = self.form.labelForField(field)
            if label_widget is not None:
                label_widget.setVisible(visible)
            field.blockSignals(False)
        self.refresh_preview()

    def current_configuration(self) -> tuple[str, dict[str, float]]:
        sample_type = self.owner.simulation_sample_key(self.sample_select.currentText())
        keys = self.owner.simulation_parameter_keys(sample_type)
        return sample_type, {key: self.fields[key].value() for key in keys}

    def refresh_preview(self) -> None:
        sample_type, params = self.current_configuration()
        sample = SampleGenerator(sample_type, params)
        center_x, center_y = params.get("center_x", 0.0), params.get("center_y", 0.0)
        span = max(params.get("radius", 0.0) * 2.4, params.get("width", 0.0) * 1.4,
                   params.get("lattice_constant", 0.0) * 8.0, params.get("lattice_constant_a", 0.0) * 8.0, 2.0)
        count = 40
        lines: list[list[dict[str, float]]] = []
        for row in range(count):
            y = center_y - span / 2 + span * row / (count - 1)
            line = []
            for column in range(count):
                x = center_x - span / 2 + span * column / (count - 1)
                height = sample.get_height_at_position(x, y)
                line.append({"x": x, "y": y, "z_feedback": height, "surface_height": height})
            lines.append(line)
        self.preview.set_scan_data(lines, [])

    def apply(self) -> None:
        sample_type, params = self.current_configuration()
        self.owner.apply_simulation_configuration(sample_type, params)
        self.accept()


class ZScannerWindow(ToolWindow):
    def __init__(self, owner: "OperatorWorkstation") -> None:
        super().__init__(owner)
        self.owner = owner
        self.setWindowTitle("Scan Control")
        self.resize(1460, 900)
        self.setMinimumSize(1180, 760)
        self.setStyleSheet(
            "QGroupBox { font-weight: 600; border: 1px solid #a8b3c2; border-radius: 4px; margin-top: 10px; padding-top: 8px; }"
            "QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; }"
            "QPushButton { min-height: 30px; } QLabel#sectionTitle { font-size: 15px; font-weight: 700; color: #18324a; }"
        )
        layout = QVBoxLayout()

        command_bar = QFrame()
        command_bar.setFrameShape(QFrame.Shape.StyledPanel)
        command_layout = QHBoxLayout(command_bar)
        title = QLabel("SCAN CONTROL · MK4S + CRTouch")
        title.setObjectName("sectionTitle")
        self.hardware_badge = QLabel("Hardware: Disconnected")
        self.motion_badge = QLabel("Motion: Locked")
        self.acquisition_badge = QLabel("Acquisition: Idle")
        self.simulation_badge = QLabel("SIMULATION")
        self.simulation_badge.setStyleSheet("padding:6px 10px; font-weight:800; color:#052e16; background:#86efac; border:1px solid #15803d;")
        for badge in (self.hardware_badge, self.motion_badge, self.acquisition_badge):
            badge.setStyleSheet("padding:6px 10px; border:1px solid #8da2b8; border-radius:3px; background:#f8fbff;")
        emergency = QPushButton("EMERGENCY STOP")
        emergency.setStyleSheet(RED_BUTTON_STYLE)
        emergency.clicked.connect(owner.stop_z)
        command_layout.addWidget(title)
        command_layout.addStretch(1)
        command_layout.addWidget(self.hardware_badge)
        command_layout.addWidget(self.motion_badge)
        command_layout.addWidget(self.acquisition_badge)
        command_layout.addWidget(self.simulation_badge)
        command_layout.addWidget(emergency)
        layout.addWidget(command_bar)

        simulation_bar = QGroupBox("Virtual Scanner")
        simulation_layout = QHBoxLayout(simulation_bar)
        self.simulation_toggle = QCheckBox("Use Simulation")
        self.simulation_toggle.setChecked(True)
        self.simulation_toggle.setToolTip("Routes every scan point through the virtual engine; no serial or G-code is used.")
        self.simulation_sample = QComboBox()
        self.simulation_sample.addItems([owner.simulation_sample_label(name) for name in SampleGenerator.SAMPLE_TYPES])
        configure_sample = QPushButton("Configure Sample…")
        configure_sample.clicked.connect(owner.open_simulation_configuration)
        self.simulation_toggle.toggled.connect(owner.set_simulation_enabled)
        self.simulation_sample.currentTextChanged.connect(owner.select_simulation_sample)
        simulation_layout.addWidget(self.simulation_toggle)
        simulation_layout.addWidget(QLabel("Sample"))
        simulation_layout.addWidget(self.simulation_sample, 1)
        simulation_layout.addWidget(configure_sample)
        layout.addWidget(simulation_bar)

        workspace = QSplitter(Qt.Orientation.Horizontal)
        z_page = QWidget()
        z_layout = QVBoxLayout(z_page)
        z_heading = QLabel("Z Scanner · Approach & Feedback")
        z_heading.setObjectName("sectionTitle")
        z_subtitle = QLabel("Live Z position, approach envelope, setpoint controls, and retract safety")
        z_subtitle.setStyleSheet("color:#52606d;")
        z_layout.addWidget(z_heading)
        z_layout.addWidget(z_subtitle)
        self.z_lockout_banner = QLabel("⚠ LOCKOUT: Connect the MK4S and authorize motion before using approach controls.")
        self.z_lockout_banner.setWordWrap(True)
        self.z_lockout_banner.setStyleSheet("font-weight:700; color:white; background:#a71919; padding:8px;")
        z_layout.addWidget(self.z_lockout_banner)
        z_layout.addWidget(owner.build_z_panel(), 1)
        workspace.addWidget(z_page)

        owner.measurement_window = MeasurementWindow(owner)
        xy_page = QWidget()
        xy_layout = QVBoxLayout(xy_page)
        xy_heading = QLabel("XY Scanner · Raster Acquisition")
        xy_heading.setObjectName("sectionTitle")
        xy_subtitle = QLabel("Applied scan geometry, acquisition channels, live line data, and map assembly")
        xy_subtitle.setStyleSheet("color:#52606d;")
        xy_layout.addWidget(xy_heading)
        xy_layout.addWidget(xy_subtitle)

        parameters = QGroupBox("Applied Scan Parameters")
        parameter_grid = QGridLayout()
        source = owner.measurement_window
        constraints = source.constraints
        self.scan_mode_input = QComboBox()
        self.scan_mode_input.addItems(["Tapping", "Constant-height"])
        self.scan_mode_input.setCurrentText("Tapping" if source.tapping_mode.isChecked() else "Constant-height")
        self.center_x_input = QDoubleSpinBox()
        self.center_y_input = QDoubleSpinBox()
        self.size_x_input = QDoubleSpinBox()
        self.size_y_input = QDoubleSpinBox()
        self.resolution_input = QSpinBox()
        self.rotation_input = QDoubleSpinBox()
        self.speed_input = QDoubleSpinBox()
        self.direction_input = QComboBox()
        self.center_x_input.setRange(constraints.x_probe_min, constraints.x_probe_max)
        self.center_y_input.setRange(constraints.y_probe_min, constraints.y_probe_max)
        self.size_x_input.setRange(0.1, constraints.x_probe_max - constraints.x_probe_min)
        self.size_y_input.setRange(0.1, constraints.y_probe_max - constraints.y_probe_min)
        self.resolution_input.setRange(constraints.resolution_min, constraints.resolution_max)
        self.rotation_input.setRange(constraints.rotation_min, constraints.rotation_max)
        self.rotation_input.setDecimals(1)
        self.rotation_input.setSuffix(" deg")
        self.speed_input.setRange(1.0, 10.0)
        self.speed_input.setDecimals(2)
        self.direction_input.addItems(["X+", "X-", "Y+", "Y-"])
        for target, original in (
            (self.center_x_input, source.x_origin), (self.center_y_input, source.y_origin),
            (self.size_x_input, source.x_size), (self.size_y_input, source.y_size),
            (self.resolution_input, source.resolution), (self.rotation_input, source.rotation),
            (self.speed_input, source.scan_speed),
        ):
            target.setValue(original.value())
        self.direction_input.setCurrentText(source.scan_direction.currentText())
        parameter_grid.addWidget(QLabel("Mode"), 0, 0)
        parameter_grid.addWidget(self.scan_mode_input, 0, 1)
        parameter_grid.addWidget(QLabel("Resolution (points/axis)"), 0, 2)
        parameter_grid.addWidget(self.resolution_input, 0, 3)
        parameter_grid.addWidget(QLabel("Center X (mm)"), 1, 0)
        parameter_grid.addWidget(self.center_x_input, 1, 1)
        parameter_grid.addWidget(QLabel("Center Y (mm)"), 1, 2)
        parameter_grid.addWidget(self.center_y_input, 1, 3)
        parameter_grid.addWidget(QLabel("Size X (mm)"), 2, 0)
        parameter_grid.addWidget(self.size_x_input, 2, 1)
        parameter_grid.addWidget(QLabel("Size Y (mm)"), 2, 2)
        parameter_grid.addWidget(self.size_y_input, 2, 3)
        parameter_grid.addWidget(QLabel("Rotation"), 3, 0)
        parameter_grid.addWidget(self.rotation_input, 3, 1)
        parameter_grid.addWidget(QLabel("Speed (mm/s)"), 3, 2)
        parameter_grid.addWidget(self.speed_input, 3, 3)
        parameter_grid.addWidget(QLabel("Direction"), 4, 0)
        parameter_grid.addWidget(self.direction_input, 4, 1)
        apply_parameters = QPushButton("Apply & Validate")
        apply_parameters.setStyleSheet(YELLOW_BUTTON_STYLE)
        apply_parameters.clicked.connect(self.apply_inline_scan_parameters)
        parameter_grid.addWidget(apply_parameters, 4, 2, 1, 2)
        parameters.setLayout(parameter_grid)
        xy_layout.addWidget(parameters)

        header = QHBoxLayout()
        self.xy_summary = QLabel()
        self.xy_summary.setWordWrap(True)
        self.xy_summary.setStyleSheet("border:1px solid #8da2b8; padding:10px; background:#f8fbff;")
        header.addWidget(self.xy_summary, 1)
        xy_layout.addLayout(header)

        channel_bar = QHBoxLayout()
        self.acquisition_mode = QComboBox()
        self.acquisition_mode.addItems(["Simulation", "Dry Run", "Real Scan"])
        self.acquisition_mode.setToolTip(
            "Simulation: software-only virtual movement and signals. Dry Run: exercise the complete scan workflow "
            "with a virtual sample and simulated probe; no G-code is sent and no CR-Touch is required. "
            "Real Scan: hardware motion and a physical sample."
        )
        self.acquisition_mode.currentTextChanged.connect(owner.set_acquisition_mode)
        self.speed_profile = QComboBox()
        self.speed_profile.addItems(["Synchronized", "Fast", "Extreme"])
        self.speed_profile.setCurrentText("Fast")
        self.primary_channel = QComboBox()
        self.primary_channel.addItems(["Height / Z Feedback", "CRTouch Interaction Proxy", "Error Channel", "Trigger Repeatability"])
        self.view_direction = QComboBox()
        self.view_direction.addItems(["Fast Axis X", "Fast Axis Y", "Serpentine Order"])
        self.live_view = QCheckBox("Live Update")
        self.live_view.setChecked(True)
        channel_bar.addWidget(QLabel("Acquisition"))
        channel_bar.addWidget(self.acquisition_mode)
        channel_bar.addWidget(QLabel("Display Rate"))
        channel_bar.addWidget(self.speed_profile)
        channel_bar.addWidget(QLabel("Primary Channel"))
        channel_bar.addWidget(self.primary_channel, 1)
        channel_bar.addWidget(QLabel("Line View"))
        channel_bar.addWidget(self.view_direction)
        channel_bar.addWidget(self.live_view)
        xy_layout.addLayout(channel_bar)

        actions = QHBoxLayout()
        start = QPushButton("Start Scan")
        start.setStyleSheet(GREEN_BUTTON_STYLE)
        start.clicked.connect(owner.start_scan_from_main)
        pause = QPushButton("Pause")
        pause.clicked.connect(owner.pause_measurement)
        stop = QPushButton("Stop Scan")
        stop.setStyleSheet(RED_BUTTON_STYLE)
        stop.clicked.connect(owner.stop_measurement)
        for button in (start, pause, stop):
            actions.addWidget(button)
        owner.xy_motion_buttons = (start, pause, stop)
        xy_layout.addLayout(actions)

        progress_row = QHBoxLayout()
        self.scan_progress = QProgressBar()
        self.scan_progress.setRange(0, 100)
        self.scan_progress.setValue(0)
        self.scan_progress.setFormat("Idle · %p%")
        self.point_readout = QLabel("Line — / — · Point — / — · X — · Y —")
        progress_row.addWidget(self.scan_progress, 1)
        progress_row.addWidget(self.point_readout)
        xy_layout.addLayout(progress_row)

        previews = QHBoxLayout()
        self.line_preview = SignalPlotWidget("Live Line Channel", "line", "X+")
        self.topography_preview = SignalPlotWidget("Topography / Contrast Map", "topography", "X+")
        previews.addWidget(self.line_preview)
        previews.addWidget(self.topography_preview)
        xy_layout.addLayout(previews, 1)
        workspace.addWidget(xy_page)
        workspace.setSizes([660, 780])
        workspace.setStretchFactor(0, 1)
        workspace.setStretchFactor(1, 1)
        layout.addWidget(workspace, 1)

        self.session_message = QLabel(
            "Ready. Verify Z safety and XY parameters before acquisition. "
            "CRTouch operation is a teaching approximation, not continuous AFM feedback."
        )
        self.session_message.setWordWrap(True)
        self.session_message.setStyleSheet("padding:8px; background:#eef4fa; border:1px solid #8da2b8;")
        layout.addWidget(self.session_message)
        self.setLayout(layout)
        owner.set_simulation_enabled(True)

    def update_instrument_state(self, *, connected: bool, motion_enabled: bool, acquisition: str = "Idle") -> None:
        self.hardware_badge.setText(f"Hardware: {'Connected' if connected else 'Disconnected'}")
        self.hardware_badge.setStyleSheet(
            "padding:6px 10px; border:1px solid #167a3a; background:#effaf2;" if connected
            else "padding:6px 10px; border:1px solid #8da2b8; background:#f8fbff;"
        )
        self.motion_badge.setText(f"Motion: {'Enabled' if motion_enabled else 'Locked'}")
        self.acquisition_badge.setText(f"Acquisition: {acquisition}")

    def apply_inline_scan_parameters(self) -> bool:
        target = self.owner.measurement_window
        if target is None:
            return False
        target.tapping_mode.setChecked(self.scan_mode_input.currentText() == "Tapping")
        target.constant_height_mode.setChecked(self.scan_mode_input.currentText() == "Constant-height")
        target.x_origin.setValue(self.center_x_input.value())
        target.y_origin.setValue(self.center_y_input.value())
        target.x_size.setValue(self.size_x_input.value())
        target.y_size.setValue(self.size_y_input.value())
        target.resolution.setValue(self.resolution_input.value())
        target.rotation.setValue(self.rotation_input.value())
        target.scan_speed.setValue(self.speed_input.value())
        target.scan_direction.setCurrentText(self.direction_input.currentText())
        if target.apply_settings():
            self.session_message.setText("Scan parameters validated and applied. Review motion authorization before Start Scan.")
            self.owner.append_log("[SCAN SETUP] Inline Scan Control parameters validated and applied.")
            return True
        else:
            self.session_message.setText(f"Parameter validation failed: {target.status.text()}")
            return False

    def set_motion_interlocks(self, *, connected: bool, standby: bool, operational: bool) -> None:
        simulation = self.owner.simulation_engine.is_active
        self.z_lockout_banner.setVisible(not standby and not simulation)
        if simulation:
            self.z_lockout_banner.setText("SIMULATION: virtual XYZ, feedback, and sample are active. No hardware commands are routed.")
            self.z_lockout_banner.setStyleSheet("font-weight:700; color:#052e16; background:#86efac; padding:8px;")
        elif standby:
            self.z_lockout_banner.setText("Z motion authorized for supervised approach and retract operations.")
            self.z_lockout_banner.setStyleSheet("font-weight:700; color:#083b25; background:#b9f4d3; padding:8px;")
        else:
            self.z_lockout_banner.setText(
                "⚠ LOCKOUT: Connect the MK4S and select STANDBY or OPERATIONAL to enable approach controls."
            )
            self.z_lockout_banner.setStyleSheet("font-weight:700; color:white; background:#a71919; padding:8px;")
        for button in getattr(self.owner, "z_motion_buttons", ()):
            button.setEnabled(standby or simulation)
            if not standby and not simulation:
                button.setToolTip("Requires an MK4S connection and STANDBY or OPERATIONAL authorization.")
        for button in getattr(self.owner, "xy_motion_buttons", ()):
            button.setEnabled(operational or simulation)
            if not operational and not simulation:
                button.setToolTip("Requires an MK4S connection and OPERATIONAL authorization.")
        self.update_instrument_state(connected=connected, motion_enabled=standby and not simulation,
                                     acquisition="Simulation Ready" if simulation else "Idle")


class LiveLogWindow(ToolWindow):
    def __init__(self, owner: "OperatorWorkstation") -> None:
        super().__init__(owner)
        self.setWindowTitle("SPM Operator — Live Log")
        self.resize(980, 460)
        layout = QVBoxLayout()
        layout.addWidget(owner.build_log_panel())
        self.setLayout(layout)


class AcademicGCodeWindow(ToolWindow):
    def __init__(self, owner: "OperatorWorkstation") -> None:
        super().__init__(owner)
        self.owner = owner
        self.accepted_request: GCodePatternRequest | None = None
        self.generated_file_text = ""
        self.generated_extension = "obj"
        self.learning_path = PROJECT_ROOT / "config" / "academic_ai_print_learning_notes.txt"
        self.chat_history: list[dict[str, str]] = []
        self.chat_turn_count = 0
        self.setWindowTitle("Local AI Print File Studio")
        self.resize(1220, 920)
        layout = QVBoxLayout()

        title = QLabel("Local AI Print File Studio")
        title.setStyleSheet("font-size: 22px; font-weight: 800; color: #d7e6f8; background: #101827; padding: 12px;")
        layout.addWidget(title)

        idea_box = QGroupBox("2. AI Build Request")
        idea_layout = QVBoxLayout()
        self.prompt = QTextEdit()
        self.prompt.setMaximumHeight(82)
        self.prompt.setPlaceholderText(
            "Example: Create a 3x3 gold-like atomic island field, 35 mm wide, thin single-layer print, "
            "with a hexagonal lattice feeling and safe travel moves."
        )
        self.prompt.setStyleSheet("color: #d7e6f8; background: #07111f; border: 1px solid #3a5878; padding: 8px;")
        idea_layout.addWidget(QLabel("What do you want to build?"))
        idea_layout.addWidget(self.prompt)
        idea_box.setLayout(idea_layout)

        form_box = QGroupBox("1. Printer Parameters")
        form = QGridLayout()
        form.setContentsMargins(8, 8, 8, 8)
        form.setHorizontalSpacing(8)
        form.setVerticalSpacing(5)
        self.size_mm = QDoubleSpinBox()
        self.size_mm.setRange(1.0, 180.0)
        self.size_mm.setDecimals(2)
        self.size_mm.setValue(35.0)
        self.thickness_mm = QDoubleSpinBox()
        self.thickness_mm.setRange(0.05, 2.0)
        self.thickness_mm.setDecimals(3)
        self.thickness_mm.setValue(0.20)
        self.feedrate = QDoubleSpinBox()
        self.feedrate.setRange(60.0, 6000.0)
        self.feedrate.setDecimals(0)
        self.feedrate.setValue(1200.0)
        self.material = QComboBox()
        self.material.addItems(["PLA", "PETG", "ABS/ASA", "TPU", "Other"])
        self.nozzle_diameter = QDoubleSpinBox()
        self.nozzle_diameter.setRange(0.10, 1.20)
        self.nozzle_diameter.setDecimals(2)
        self.nozzle_diameter.setSingleStep(0.05)
        self.nozzle_diameter.setValue(0.40)
        self.nozzle_temperature = QSpinBox()
        self.nozzle_temperature.setRange(0, 320)
        self.nozzle_temperature.setValue(215)
        self.bed_temperature = QSpinBox()
        self.bed_temperature.setRange(0, 140)
        self.bed_temperature.setValue(60)
        self.line_spacing = QDoubleSpinBox()
        self.line_spacing.setRange(0.2, 30.0)
        self.line_spacing.setDecimals(2)
        self.line_spacing.setValue(2.5)
        self.output_format = QComboBox()
        self.output_format.addItems(["obj", "stl", "gcode"])
        self.output_format.setCurrentText("obj")
        compact_controls = [
            ("Size mm", self.size_mm),
            ("Layer Z mm", self.thickness_mm),
            ("Material", self.material),
            ("Nozzle mm", self.nozzle_diameter),
            ("Nozzle C", self.nozzle_temperature),
            ("Bed C", self.bed_temperature),
            ("Feed mm/min", self.feedrate),
            ("Spacing mm", self.line_spacing),
            ("Export", self.output_format),
        ]
        for index, (label_text, widget) in enumerate(compact_controls):
            row = index // 3
            col = (index % 3) * 2
            label = QLabel(label_text)
            label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            widget.setMinimumHeight(28)
            form.addWidget(label, row, col)
            form.addWidget(widget, row, col + 1)
        form_box.setLayout(form)
        layout.addWidget(form_box)
        layout.addWidget(idea_box)

        discussion_box = QGroupBox("3. Interactive AI Discussion")
        discussion_layout = QVBoxLayout()
        self.chat_transcript = QTextEdit()
        self.chat_transcript.setReadOnly(True)
        self.chat_transcript.setMinimumHeight(260)
        self.chat_transcript.setStyleSheet("font-family: Segoe UI, Arial; background: #f8fbff;")
        self.chat_transcript.setPlainText(
            "Set printer parameters first. Then write a request and click Send to AI.\n"
            "Discuss until the plan is right. The studio supports 10+ refinement rounds before final confirmation."
        )
        self.refinement_notes = QTextEdit()
        self.refinement_notes.setMaximumHeight(86)
        self.refinement_notes.setPlaceholderText(
            "Message to AI. Example: make it thinner, suggest safer PETG parameters, or simplify the geometry."
        )
        discussion_layout.addWidget(self.chat_transcript)
        discussion_layout.addWidget(self.refinement_notes)
        discussion_box.setLayout(discussion_layout)
        layout.addWidget(discussion_box)

        learning_box = QGroupBox("Learning Notes")
        learning_layout = QHBoxLayout()
        learning_layout.setContentsMargins(8, 8, 8, 8)
        self.learning_notes = QTextEdit()
        self.learning_notes.setMaximumHeight(58)
        self.learning_notes.setPlaceholderText(
            "Optional: save preferences here, for example preferred material, good sizes, failed ideas, or printer-specific habits."
        )
        self.learning_notes.setPlainText(self.load_learning_notes())
        learning_layout.addWidget(self.learning_notes)
        save_learning = QPushButton("Save Learning Notes")
        save_learning.setMinimumHeight(34)
        save_learning.clicked.connect(self.save_learning_notes)
        learning_layout.addWidget(save_learning)
        learning_box.setLayout(learning_layout)
        layout.addWidget(learning_box)

        actions = QHBoxLayout()
        ask_ai = QPushButton("Send to AI")
        improve = QPushButton("Use AI Suggested Parameters")
        accept = QPushButton("Confirm Final")
        self.generate_button = QPushButton("Create Code")
        self.save_button = QPushButton("Save As")
        self.code_button = QPushButton("Show Code")
        for button in (ask_ai, improve, accept, self.generate_button, self.save_button):
            button.setStyleSheet(GREEN_BUTTON_STYLE)
        self.generate_button.setEnabled(False)
        self.save_button.setEnabled(False)
        ask_ai.clicked.connect(self.send_ai_message)
        improve.clicked.connect(self.apply_ai_suggested_parameters)
        accept.clicked.connect(self.accept_plan)
        self.generate_button.clicked.connect(self.generate_gcode)
        self.save_button.clicked.connect(self.save_gcode)
        self.code_button.clicked.connect(self.toggle_code_view)
        actions.addWidget(ask_ai)
        actions.addWidget(improve)
        actions.addWidget(accept)
        actions.addWidget(self.generate_button)
        actions.addWidget(self.save_button)
        actions.addWidget(self.code_button)
        layout.addLayout(actions)

        self.status = QLabel(
            "Describe the surface or microstructure you want. Default export is OBJ/STL, which PrusaSlicer can import. "
            "G-code is expert-only and opens through G-code Preview. Nothing is sent to hardware."
        )
        self.status.setWordWrap(True)
        self.status.setStyleSheet("border: 1px solid #3a5878; padding: 10px; background: #0b1624; color: #d7e6f8;")
        layout.addWidget(self.status)
        self.instructions = QLabel(
            "PrusaSlicer workflow: Save OBJ or STL -> File -> Import -> Import STL/3MF/STEP/OBJ/AMF. "
            "For .gcode use File -> G-code Preview. Slice/export print G-code from PrusaSlicer."
        )
        self.instructions.setWordWrap(True)
        self.instructions.setStyleSheet("border: 1px solid #8da2b8; padding: 8px; background: #f8fbff;")
        layout.addWidget(self.instructions)

        workspace = QSplitter(Qt.Orientation.Vertical)
        workspace.setChildrenCollapsible(False)
        self.plan_view = QTextEdit()
        self.plan_view.setReadOnly(True)
        self.plan_view.setStyleSheet("font-family: Segoe UI, Arial; background: #f8fbff;")
        self.plan_view.setPlainText(
            "Step 1: set printer parameters.\n"
            "Step 2: write the build request or parameter question.\n"
            "Step 3: click Send to AI and discuss until the plan is correct.\n"
            "Step 4: click Confirm Final, then Create Code, then Save As.\n\n"
            "No generated file is sent to hardware from this window."
        )
        workspace.addWidget(self.plan_view)
        self.code_view = QTextEdit()
        self.code_view.setReadOnly(True)
        self.code_view.setVisible(False)
        self.code_view.setStyleSheet("font-family: Consolas, monospace; background: #07111f; color: #d7e6f8;")
        workspace.addWidget(self.code_view)
        workspace.setSizes([420, 220])
        layout.addWidget(workspace, 1)
        self.setLayout(layout)

    def load_learning_notes(self) -> str:
        if not self.learning_path.exists():
            return ""
        return self.learning_path.read_text(encoding="utf-8").strip()

    def save_learning_notes(self) -> None:
        self.learning_path.parent.mkdir(parents=True, exist_ok=True)
        self.learning_path.write_text(self.learning_notes.toPlainText().strip() + "\n", encoding="utf-8")
        self.status.setText("Learning notes saved. Future AI build plans will include these local preferences.")
        self.owner.append_log("[ACADEMIC EXPORT] Learning notes saved locally.")

    def toggle_code_view(self) -> None:
        visible = not self.code_view.isVisible()
        self.code_view.setVisible(visible)
        self.code_button.setText("Hide Code" if visible else "Show Code")

    def printer_parameter_context(self) -> dict[str, Any]:
        return {
            "material": str(self.material.currentText()),
            "nozzle_diameter_mm": float(self.nozzle_diameter.value()),
            "nozzle_temperature_c": int(self.nozzle_temperature.value()),
            "bed_temperature_c": int(self.bed_temperature.value()),
            "size_mm": float(self.size_mm.value()),
            "thickness_mm": float(self.thickness_mm.value()),
            "feedrate_mm_min": float(self.feedrate.value()),
            "line_spacing_mm": float(self.line_spacing.value()),
            "output_format": str(self.output_format.currentText()),
        }

    def append_chat(self, role: str, message: str) -> None:
        clean = message.strip()
        if not clean:
            return
        self.chat_history.append({"role": role, "message": clean})
        lines = [f"{item['role'].upper()}\n{item['message']}" for item in self.chat_history[-24:]]
        self.chat_transcript.setPlainText("\n\n".join(lines))
        self.chat_transcript.verticalScrollBar().setValue(self.chat_transcript.verticalScrollBar().maximum())

    def apply_ai_suggested_parameters(self) -> None:
        text = f"{self.prompt.toPlainText()} {self.refinement_notes.toPlainText()}".lower()
        if "petg" in text:
            self.material.setCurrentText("PETG")
            self.nozzle_temperature.setValue(240)
            self.bed_temperature.setValue(85)
            self.feedrate.setValue(900)
        elif "abs" in text or "asa" in text:
            self.material.setCurrentText("ABS/ASA")
            self.nozzle_temperature.setValue(255)
            self.bed_temperature.setValue(100)
            self.feedrate.setValue(850)
        elif "tpu" in text or "flex" in text:
            self.material.setCurrentText("TPU")
            self.nozzle_temperature.setValue(225)
            self.bed_temperature.setValue(50)
            self.feedrate.setValue(450)
        else:
            self.material.setCurrentText("PLA")
            self.nozzle_temperature.setValue(215)
            self.bed_temperature.setValue(60)
            self.feedrate.setValue(1200)

        if "thin" in text or "fine" in text or "detail" in text:
            self.thickness_mm.setValue(0.12)
            self.line_spacing.setValue(1.2)
        if "strong" in text or "thick" in text:
            self.thickness_mm.setValue(0.28)
            self.line_spacing.setValue(2.4)
        self.status.setText("AI-suggested printer parameters applied. Review them, then Send to AI.")
        self.owner.append_log("[ACADEMIC EXPORT] AI-suggested printer parameters applied locally.")

    def request(self) -> GCodePatternRequest:
        return GCodePatternRequest(
            prompt=self.prompt.toPlainText().strip()
            or "Create a 3x3 gold-like atomic island field with small hexagonal rings.",
            pattern="auto",
            refinement_notes=self.refinement_notes.toPlainText().strip(),
            learning_notes=self.learning_notes.toPlainText().strip(),
            material=str(self.material.currentText()),
            nozzle_diameter_mm=float(self.nozzle_diameter.value()),
            nozzle_temperature_c=int(self.nozzle_temperature.value()),
            bed_temperature_c=int(self.bed_temperature.value()),
            size_mm=float(self.size_mm.value()),
            thickness_mm=float(self.thickness_mm.value()),
            feedrate_mm_min=float(self.feedrate.value()),
            line_spacing_mm=float(self.line_spacing.value()),
            output_format=str(self.output_format.currentText()),
        )

    def send_ai_message(self) -> None:
        message = self.refinement_notes.toPlainText().strip() or self.prompt.toPlainText().strip()
        if not message:
            QMessageBox.warning(self, "Input required", "Write what you want to build or ask AI to suggest printer parameters.")
            return
        self.append_chat("User", message)
        self.chat_turn_count += 1
        self.ask_ai_for_plan(chat_message=message)
        self.refinement_notes.clear()

    def ask_ai_for_plan(self, chat_message: str = "") -> None:
        try:
            plan = build_gcode_plan(self.request())
        except ValueError as exc:
            QMessageBox.warning(self, "Print file request invalid", str(exc))
            return
        advice = build_ai_recommendation(
            task="refine user wish into review-only print model build plan",
            context={
                "prompt": plan.request.prompt,
                "refinement_notes": plan.request.refinement_notes,
                "learning_notes": plan.request.learning_notes,
                "resolved_pattern": plan.resolved_pattern,
                "material": plan.request.material,
                "nozzle_diameter_mm": plan.request.nozzle_diameter_mm,
                "nozzle_temperature_c": plan.request.nozzle_temperature_c,
                "bed_temperature_c": plan.request.bed_temperature_c,
                "size_mm": plan.request.size_mm,
                "thickness_mm": plan.request.thickness_mm,
                "feedrate_mm_min": plan.request.feedrate_mm_min,
                "line_spacing_mm": plan.request.line_spacing_mm,
                "printer_parameters": self.printer_parameter_context(),
                "chat_message": chat_message,
                "chat_history": self.chat_history[-20:],
                "turn_count": self.chat_turn_count,
                "minimum_supported_discussion_rounds": 10,
                "execution_allowed": False,
            },
        )
        recommendations = advice.get("recommendation", []) if isinstance(advice, dict) else []
        ai_text = "\n".join(f"- {item}" for item in recommendations[:5]) or "- Review the local plan and refine the request."
        self.append_chat("AI", ai_text)
        self.accepted_request = None
        self.generated_file_text = ""
        self.generate_button.setEnabled(False)
        self.save_button.setEnabled(False)
        self.plan_view.setPlainText(
            f"Candidate plan after discussion round {self.chat_turn_count}\n"
            + plan.summary
            + "\n\nAI notes\n- "
            + "\n- ".join(str(item) for item in recommendations[:5])
            + "\n\nCheck before agreeing\n- "
            + "\n- ".join(plan.operator_questions)
            + "\n\nAfter saving\n- "
            + "\n- ".join(plan.review_steps)
        )
        self.status.setText("AI answered. Continue discussing, use suggested parameters, or Confirm Final when the plan is correct.")
        self.owner.append_log(f"[ACADEMIC EXPORT] AI discussion round {self.chat_turn_count}; no file generated yet.")

    def accept_plan(self) -> None:
        try:
            plan = build_gcode_plan(self.request())
        except ValueError as exc:
            QMessageBox.warning(self, "Print file request invalid", str(exc))
            return
        self.accepted_request = plan.request
        self.generated_file_text = ""
        self.generated_extension = plan.request.output_format
        self.generate_button.setEnabled(True)
        self.save_button.setEnabled(False)
        self.plan_view.append("\n\nFINAL PLAN CONFIRMED. Click Create Code when ready.")
        self.status.setText("Final build plan confirmed. Create Code is now enabled; no file has been created or sent.")

    def generate_gcode(self) -> None:
        if self.accepted_request is None:
            QMessageBox.warning(
                self,
                "Plan required",
                "Click Send to AI, discuss the plan if needed, and click Confirm Final before creating code.",
            )
            return
        try:
            payload = build_academic_gcode_job(self.accepted_request)
        except ValueError as exc:
            QMessageBox.warning(self, "Print file request invalid", str(exc))
            return
        self.generated_file_text = str(payload["file_text"])
        self.generated_extension = str(payload["file_extension"])
        self.code_view.setPlainText(self.generated_file_text)
        self.save_button.setEnabled(True)
        self.plan_view.append(
            f"\n\nFINAL {self.generated_extension.upper()} FILE GENERATED: {payload['line_count']} lines. "
            f"{payload['viewing_instruction']}"
        )
        self.status.setText(
            f"Created {self.generated_extension.upper()} internally. Use Save As when ready. gcode_sent=False."
        )
        self.owner.append_log(f"[ACADEMIC EXPORT] Generated review-only {self.generated_extension.upper()}; no hardware command sent.")

    def save_gcode(self) -> None:
        text = self.generated_file_text
        if not text.strip():
            QMessageBox.warning(self, "Create first", "Create Code before saving.")
            return
        suffix = self.generated_extension
        filters = "Model files (*.obj *.stl);;G-code (*.gcode);;Text (*.txt)"
        path, _filter = QFileDialog.getSaveFileName(self, "Save final review file", f"academic_ai_concept.{suffix}", filters)
        if not path:
            return
        Path(path).write_text(text, encoding="utf-8")
        self.owner.append_log(f"[ACADEMIC EXPORT] Saved review file: {path}")
        self.status.setText(f"Saved review-only {suffix.upper()} to {path}. It was not sent to hardware.")


class CRTouchPrepWindow(ToolWindow):
    def __init__(self, owner: "OperatorWorkstation") -> None:
        super().__init__(owner)
        self.owner = owner
        self.plan = CRTouchProbePlan()
        self.setWindowTitle("CR Touch Probe Preparation")
        self.resize(860, 620)
        layout = QVBoxLayout()
        self.summary = QTextEdit()
        self.summary.setReadOnly(True)
        self.summary.setPlainText(
            "\n\n".join(
                [
                    self.plan.readiness_summary(),
                    self.plan.safety_summary(),
                    self.plan.test_sequence_summary(),
                    self.plan.integration_checklist(),
                ]
            )
        )
        layout.addWidget(self.summary, 1)
        actions = QHBoxLayout()
        self.mega_status = QLabel(
            "Mega 2560: not tested · CR Touch actuation remains locked"
        )
        self.mega_status.setWordWrap(True)
        self.mega_status.setStyleSheet(
            "padding:8px; background:#fff7df; border:1px solid #d9a441;"
        )
        layout.addWidget(self.mega_status)
        test_mega = QPushButton("Test Mega Connection — Read Only")
        test_mega.setStyleSheet(GREEN_BUTTON_STYLE)
        test_mega.clicked.connect(owner.test_mega_probe_connection)
        actions.addWidget(test_mega)
        read_probe = QPushButton("Read MK4S Status M119")
        read_probe.setStyleSheet(GREEN_BUTTON_STYLE)
        read_probe.clicked.connect(owner.read_z)
        actions.addWidget(read_probe)
        layout.addLayout(actions)
        self.setLayout(layout)


class MeasurementWindow(ToolWindow):
    def __init__(self, owner: "OperatorWorkstation") -> None:
        super().__init__(owner)
        self.owner = owner
        self.settings = QSettings("SPM-Prusa", "OperatorTeachingEdition")
        self.motion_authorization = "LOCKED"
        self.constraints = load_scan_constraints()
        self.setWindowTitle("Scan Parameter Editor")
        self.resize(1050, 760)

        layout = QGridLayout()
        left = QVBoxLayout()
        mode_group = QGroupBox("Mode")
        mode_layout = QVBoxLayout()
        self.tapping_mode = QRadioButton("Tapping mode")
        self.constant_height_mode = QRadioButton("Constant-height mode")
        self.mode_group = QButtonGroup(self)
        self.mode_group.addButton(self.tapping_mode)
        self.mode_group.addButton(self.constant_height_mode)
        selected_mode = self.settings.value("scan/mode", "tapping")
        (self.constant_height_mode if selected_mode == "constant_height" else self.tapping_mode).setChecked(True)
        self.constant_height_mode.setToolTip("Teaching emulation: Z stays nominally fixed while CRTouch proximity is sampled.")
        self.tapping_mode.setToolTip("Teaching emulation: each pixel uses an approach–trigger–retract cycle.")
        mode_layout.addWidget(self.tapping_mode)
        mode_layout.addWidget(self.constant_height_mode)
        mode_group.setLayout(mode_layout)
        left.addWidget(mode_group)

        geometry = QGroupBox("Geometry")
        geometry_form = QFormLayout()
        self.x_size = QDoubleSpinBox()
        self.y_size = QDoubleSpinBox()
        self.x_origin = QDoubleSpinBox()
        self.y_origin = QDoubleSpinBox()
        self.resolution = QSpinBox()
        self.rotation = QDoubleSpinBox()
        self.scan_speed = QDoubleSpinBox()
        self.scan_direction = QComboBox()
        self.surface = QComboBox()
        self.resolution_status = QLabel()

        c = self.constraints
        self.x_origin.setRange(c.x_probe_min, c.x_probe_max)
        self.y_origin.setRange(c.y_probe_min, c.y_probe_max)
        self.x_origin.setValue((c.x_probe_min + c.x_probe_max) / 2.0)
        self.y_origin.setValue((c.y_probe_min + c.y_probe_max) / 2.0)
        self.x_size.setRange(0.1, c.x_probe_max - c.x_probe_min)
        self.y_size.setRange(0.1, c.y_probe_max - c.y_probe_min)
        self.x_size.setValue(20.0)
        self.y_size.setValue(20.0)
        self.resolution.setRange(c.resolution_min, c.resolution_max)
        self.resolution.setValue(int(self.settings.value("scan/resolution", c.resolution_default)))
        self.rotation.setRange(c.rotation_min, c.rotation_max)
        self.rotation.setDecimals(1)
        self.rotation.setSingleStep(0.1)
        self.rotation.setSuffix("°")
        self.rotation.setValue(float(self.settings.value("scan/rotation", 0.0)))
        self.scan_speed.setRange(1.0, 10.0)
        self.scan_speed.setDecimals(2)
        self.scan_speed.setValue(5.0)
        self.scan_direction.addItems(["X+", "X-", "Y+", "Y-"])
        self.surface.addItems(["sphere_on_plane", "terrace", "grid_atoms", "bravais_lattice"])
        for widget in (self.x_origin, self.y_origin, self.x_size, self.y_size, self.rotation):
            widget.valueChanged.connect(self.update_resolution_status)
        self.resolution.valueChanged.connect(self.update_resolution_status)
        self.scan_speed.valueChanged.connect(self.update_resolution_status)
        self.scan_direction.currentTextChanged.connect(lambda _text: self.update_resolution_status())
        reset_rotation = QPushButton("Reset to 0°")
        reset_rotation.clicked.connect(lambda: self.rotation.setValue(0.0))
        rotation_row = QHBoxLayout()
        rotation_row.addWidget(self.rotation)
        rotation_row.addWidget(reset_rotation)
        geometry_form.addRow(f"Center X [min: {c.x_probe_min:.1f}, max: {c.x_probe_max:.1f}] mm", self.x_origin)
        geometry_form.addRow(f"Center Y [min: {c.y_probe_min:.1f}, max: {c.y_probe_max:.1f}] mm", self.y_origin)
        geometry_form.addRow(f"Scan Size X [min: 0.1, max: {c.x_probe_max-c.x_probe_min:.1f}] mm", self.x_size)
        geometry_form.addRow(f"Scan Size Y [min: 0.1, max: {c.y_probe_max-c.y_probe_min:.1f}] mm", self.y_size)
        geometry_form.addRow(f"Resolution [min: {c.resolution_min}, max: {c.resolution_max}]", self.resolution)
        geometry_form.addRow(f"Rotation [min: {c.rotation_min:.0f}°, max: {c.rotation_max:.0f}°]", rotation_row)
        geometry_form.addRow("Scan Speed [min: 1, max: 10] mm/s", self.scan_speed)
        geometry_form.addRow("Scan Direction", self.scan_direction)
        geometry_form.addRow("Simulation Surface", self.surface)
        geometry.setLayout(geometry_form)
        left.addWidget(geometry)

        constraints_group = QGroupBox("Constraints")
        constraints_layout = QVBoxLayout()
        offset = QLabel(f"Probe offset: {c.dx:+.0f} mm X, {c.dy:+.0f} mm Y · Teaching safety margin: {c.safety_margin:.1f} mm")
        offset.setToolTip("Derived from MK4S limits and the configured Creality CRTouch tip offset.")
        constraints_layout.addWidget(offset)
        self.resolution_status.setWordWrap(True)
        self.resolution_status.setStyleSheet("border: 1px solid #8da2b8; padding: 8px; background: #f8fbff;")
        constraints_layout.addWidget(self.resolution_status)
        constraints_group.setLayout(constraints_layout)
        left.addWidget(constraints_group)

        actions = QVBoxLayout()
        apply_button = QPushButton("Apply")
        start = QPushButton("Start")
        stop = QPushButton("Stop")
        save = QPushButton("Save")
        cancel = QPushButton("Cancel")
        start.setStyleSheet(GREEN_BUTTON_STYLE)
        stop.setStyleSheet(RED_BUTTON_STYLE)
        apply_button.clicked.connect(self.apply_settings)
        start.clicked.connect(owner.start_scan_from_main)
        stop.clicked.connect(owner.stop_measurement)
        save.clicked.connect(self.apply_settings)
        cancel.clicked.connect(self.hide)
        for button in (apply_button, start, stop, save, cancel):
            button.setMinimumWidth(150)
            button.setMinimumHeight(38)
            actions.addWidget(button)
        actions.addStretch(1)

        layout.addLayout(left, 0, 0)
        layout.addLayout(actions, 0, 1)

        self.status = QLabel("Configure scan geometry and acquisition behavior. CRTouch feedback is a teaching approximation.")
        self.status.setWordWrap(True)
        self.status.setStyleSheet("border: 1px solid #8da2b8; padding: 8px; background: #f8fbff;")
        layout.addWidget(self.status, 1, 0, 1, 2)

        self.setLayout(layout)
        self.update_resolution_status()

    def apply_settings(self) -> bool:
        valid, message = self.validate_inputs()
        if not valid:
            self.status.setText(message)
            self.status.setStyleSheet("border: 1px solid #a71919; color: #8b0000; padding: 8px; background: #fff0f0;")
            return False
        mode = "tapping" if self.tapping_mode.isChecked() else "constant_height"
        self.settings.setValue("scan/mode", mode)
        self.settings.setValue("scan/resolution", self.resolution.value())
        self.settings.setValue("scan/rotation", self.rotation.value())
        self.owner.update_scan_summary()
        self.status.setText("Parameters applied. Scan area is within the effective probe range.")
        self.status.setStyleSheet("border: 1px solid #167a3a; padding: 8px; background: #effaf2;")
        return True

    def validate_inputs(self) -> tuple[bool, str]:
        return validate_scan_rectangle(
            center_x=self.x_origin.value(), center_y=self.y_origin.value(),
            width=self.x_size.value(), height=self.y_size.value(), rotation_deg=self.rotation.value(),
            constraints=self.constraints,
        )

    def start_selected_mode(self) -> None:
        if not self.apply_settings():
            return
        if self.tapping_mode.isChecked():
            self.start_foil_tap_scan()
        else:
            self.start_real_scan()

    def profile(self) -> WebScanProfile:
        half_x = self.x_size.value() / 2.0
        half_y = self.y_size.value() / 2.0
        return WebScanProfile(
            x_min=self.x_origin.value() - half_x,
            x_max=self.x_origin.value() + half_x,
            y_min=self.y_origin.value() - half_y,
            y_max=self.y_origin.value() + half_y,
            x_points=int(self.resolution.value()),
            y_points=int(self.resolution.value()),
            z_setpoint=float(self.owner.target_z.value()),
            feedback_gain=float(self.owner.feedback_gain.value()),
            surface=str(self.surface.currentText()),
            serpentine=True,
            scan_direction=str(self.scan_direction.currentText()),
        )

    def update_resolution_status(self) -> None:
        valid, message = self.validate_inputs()
        step_x = self.x_size.value() / max(1, self.resolution.value() - 1)
        step_y = self.y_size.value() / max(1, self.resolution.value() - 1)
        self.resolution_status.setText(
            f"{message} Pixel pitch: X {step_x:.3f} mm, Y {step_y:.3f} mm. "
            f"Limits loaded from {self.constraints.source}."
        )
        self.resolution_status.setStyleSheet(
            "border: 1px solid #167a3a; padding: 8px; background: #effaf2;" if valid
            else "border: 1px solid #a71919; color: #8b0000; padding: 8px; background: #fff0f0;"
        )

    def foil_tap_config(self) -> FoilTapConfig:
        # The contact limit is the authoritative lower travel boundary.  Keeping
        # it separate from the display/setpoint field prevents an accidental
        # default (historically Z=0) from becoming a real motion command.
        return FoilTapConfig(
            z_setpoint_mm=float(self.owner.contact_limit.value()),
            tapping_range_mm=float(self.owner.tapping_range.value()),
            approach_speed_mm_s=float(self.owner.approach_speed.value()),
            retract_after_tap_mm=float(self.owner.tap_retract_z.value()),
            full_retract_z_mm=float(self.owner.full_retract_z.value()),
        )

    def start_measurement(self) -> None:
        if self.owner.start_measurement_simulation(self.profile(), self.scan_speed.value()):
            self.status.setText("Teaching simulation running. Line and map channels update point by point.")

    def start_real_scan(self) -> None:
        if self.owner.start_measurement_real_scan(self.profile(), self.scan_speed.value()):
            self.status.setText("Constant-height training scan requested; analog AFM deflection is not available.")

    def start_foil_tap_scan(self) -> None:
        if self.owner.start_measurement_foil_tap_scan(self.profile(), self.foil_tap_config(), self.scan_speed.value()):
            self.status.setText("Tapping training scan requested: approach, detect, retract, then advance XY.")

    def update_progress_views(self, lines: list[list[dict[str, float]]], current_line: list[dict[str, float]]) -> None:
        if self.owner.z_scanner_window is not None:
            self.owner.z_scanner_window.line_preview.set_scan_data(lines, current_line)
            self.owner.z_scanner_window.topography_preview.set_scan_data(lines, current_line)


class Worker(QThread):
    log_line = pyqtSignal(str)
    sample = pyqtSignal(dict)
    finished_payload = pyqtSignal(dict)

    def __init__(self, fn: Callable[[], dict[str, Any]]) -> None:
        super().__init__()
        self.fn = fn

    def run(self) -> None:
        try:
            payload = self.fn()
        except Exception as exc:  # pragma: no cover - exercised manually with hardware
            payload = {"ok": False, "message": repr(exc), "log_lines": [repr(exc)]}
        self.finished_payload.emit(payload)


class ZSetpointWorker(QThread):
    log_line = pyqtSignal(str)
    sample = pyqtSignal(dict)
    finished_payload = pyqtSignal(dict)

    def __init__(self, target_z: float) -> None:
        super().__init__()
        self.target_z = float(target_z)

    def run(self) -> None:
        try:
            if os.getenv("SPM_WEB_ALLOW_Z_MOTION", "").strip() != "1":
                self.finished_payload.emit({
                    "ok": False,
                    "message": "Z motion gate is locked. Set SPM_WEB_ALLOW_Z_MOTION=1 before launch.",
                    "log_lines": ["Z setpoint blocked: SPM_WEB_ALLOW_Z_MOTION is not enabled."],
                })
                return

            result = run_mk4s_z_move_to_setpoint(
                target_z_mm=self.target_z,
                execute=True,
                on_sample=lambda sample: self.sample.emit(dict(sample)),
            )
            self.finished_payload.emit({
                "ok": result.success,
                "message": result.message,
                "target_z": result.target_z,
                "log_lines": [result.message, *result.responses],
            })
        except Exception as exc:  # pragma: no cover - exercised manually with hardware
            self.finished_payload.emit({"ok": False, "message": repr(exc), "log_lines": [repr(exc)]})


class ZAutoApproachSimulationWorker(QThread):
    sample = pyqtSignal(dict)
    finished_payload = pyqtSignal(dict)

    def __init__(self, start_z: float, surface_z: float, clearance: float) -> None:
        super().__init__()
        self.start_z = float(start_z)
        self.surface_z = float(surface_z)
        self.clearance = float(clearance)

    def run(self) -> None:
        target_z = self.surface_z + self.clearance
        distance = target_z - self.start_z
        transition = self.start_z + distance * 0.90
        points = [self.start_z, transition]
        step = -0.25 if target_z < transition else 0.25
        z = transition
        while (step < 0 and z + step > target_z) or (step > 0 and z + step < target_z):
            z += step
            points.append(round(z, 4))
        points.append(target_z)
        for index, z_value in enumerate(points):
            self.sample.emit({"phase": "simulated_auto_approach", "z": float(z_value), "target_z": target_z})
            self.msleep(18 if index < 2 else 35)
        self.finished_payload.emit({
            "ok": True,
            "status": "simulated",
            "message": f"Simulated auto approach complete. Final Z={target_z:.3f} mm.",
            "log_lines": [
                "Auto approach is simulation-first until verified sensor feedback is installed.",
                f"Simulated fast approach to 90%, then slow final approach to Z={target_z:.3f} mm.",
            ],
        })


class RealScanWorker(QThread):
    point = pyqtSignal(dict)
    finished_payload = pyqtSignal(dict)

    def __init__(self, profile: WebScanProfile, scan_speed_mm_s: float, port: str | None) -> None:
        super().__init__()
        self.profile = profile
        self.scan_speed_mm_s = float(scan_speed_mm_s)
        self.port = port

    def run(self) -> None:
        try:
            result = run_real_constant_z_scan(
                self.profile,
                port=self.port,
                scan_speed_mm_s=self.scan_speed_mm_s,
                on_point=lambda point: self.point.emit(dict(point)),
            )
            self.finished_payload.emit(result)
        except Exception as exc:  # pragma: no cover - exercised manually with hardware
            self.finished_payload.emit({"ok": False, "status": "failed", "message": repr(exc), "log_lines": [repr(exc)]})


class FoilTapScanWorker(QThread):
    point = pyqtSignal(dict)
    finished_payload = pyqtSignal(dict)

    def __init__(self, profile: WebScanProfile, tap_config: FoilTapConfig, scan_speed_mm_s: float, port: str | None) -> None:
        super().__init__()
        self.profile = profile
        self.tap_config = tap_config
        self.scan_speed_mm_s = float(scan_speed_mm_s)
        self.port = port

    def run(self) -> None:
        try:
            result = run_real_foil_tap_scan(
                self.profile,
                self.tap_config,
                port=self.port,
                scan_speed_mm_s=self.scan_speed_mm_s,
                on_point=lambda point: self.point.emit(dict(point)),
            )
            self.finished_payload.emit(result)
        except Exception as exc:  # pragma: no cover - exercised manually with hardware
            self.finished_payload.emit({"ok": False, "status": "failed", "message": repr(exc), "log_lines": [repr(exc)]})


class HardwareDryRunWorker(QThread):
    point = pyqtSignal(dict)
    finished_payload = pyqtSignal(dict)

    def __init__(
        self,
        profile: WebScanProfile,
        sample_type: str,
        sample_params: dict[str, float],
        scan_speed_mm_s: float,
        port: str | None,
    ) -> None:
        super().__init__()
        self.profile = profile
        self.sample_type = sample_type
        self.sample_params = dict(sample_params)
        self.scan_speed_mm_s = float(scan_speed_mm_s)
        self.port = port

    def run(self) -> None:
        result = run_hardware_dry_run(
            self.profile,
            self.sample_type,
            self.sample_params,
            scan_speed_mm_s=self.scan_speed_mm_s,
            port=self.port,
            on_point=lambda point: self.point.emit(dict(point)),
        )
        self.finished_payload.emit(result)


class _WorkerSignalStream(io.TextIOBase):
    """Convert newline-delimited runner output into queued Qt signals."""

    def __init__(self, emit_line: Callable[[str], None]) -> None:
        super().__init__()
        self.emit_line = emit_line
        self._buffer = ""

    def write(self, text: str) -> int:
        self._buffer += str(text)
        while "\n" in self._buffer:
            line, self._buffer = self._buffer.split("\n", 1)
            if line.strip():
                self.emit_line(line.rstrip())
        return len(text)

    def flush(self) -> None:
        if self._buffer.strip():
            self.emit_line(self._buffer.rstrip())
        self._buffer = ""


class TwoObjectAdaptiveScanWorker(QThread):
    """Run adaptive raised-object discovery without blocking the UI."""

    log_line = pyqtSignal(str)
    finished_payload = pyqtSignal(dict)

    def __init__(self, resolution: str) -> None:
        super().__init__()
        self.resolution = resolution

    def run(self) -> None:
        output_dir = PROJECT_ROOT / "data" / "crtouch_profiles"
        before = set(output_dir.glob("verified_two_magnet_map_*_summary.json"))
        stream = _WorkerSignalStream(self.log_line.emit)
        try:
            with contextlib.redirect_stdout(stream), contextlib.redirect_stderr(stream):
                exit_code = int(run_verified_two_magnet_map(self.resolution))
            stream.flush()
            created = sorted(
                set(output_dir.glob("verified_two_magnet_map_*_summary.json")) - before,
                key=lambda path: path.stat().st_mtime,
            )
            summary_path = created[-1] if created else None
            summary = (
                json.loads(summary_path.read_text(encoding="utf-8"))
                if summary_path is not None
                else {}
            )
            self.finished_payload.emit(
                {
                    "ok": exit_code == 0 and summary.get("status") == "PASS",
                    "status": summary.get("status", "FAILED"),
                    "message": (
                        "Adaptive raised-object scan completed and retracted safely."
                        if exit_code == 0
                        else f"Adaptive object scan stopped with exit code {exit_code}."
                    ),
                    "summary": summary,
                    "summary_path": str(summary_path) if summary_path else "",
                }
            )
        except Exception as exc:  # pragma: no cover - real hardware path
            stream.flush()
            self.finished_payload.emit(
                {
                    "ok": False,
                    "status": "FAILED",
                    "message": repr(exc),
                    "summary": {},
                    "summary_path": "",
                }
            )


class OperatorWorkstation(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.resize(1500, 900)
        self.setMinimumSize(1180, 760)
        self.settings = QSettings("SPM-Prusa", "OperatorTeachingEdition")
        self.worker: QThread | None = None
        self.last_system_payload: dict[str, Any] = {}
        self.latest_z_value = 120.0
        self.z_scanner_window: ZScannerWindow | None = None
        self.live_log_window: LiveLogWindow | None = None
        self.academic_gcode_window: AcademicGCodeWindow | None = None
        self.crtouch_prep_window: CRTouchPrepWindow | None = None
        self.measurement_window: MeasurementWindow | None = None
        self.latest_two_object_result: dict[str, Any] = {}
        self.signal_windows: dict[str, QDialog] = {}
        self.signal_plots: dict[str, SignalPlotWidget] = {}
        self.measurement_timer = QTimer(self)
        self.measurement_timer.timeout.connect(self.advance_measurement_batch)
        self.measurement_batch_size = 1
        self.measurement_profile: WebScanProfile | None = None
        self.measurement_lines: list[list[dict[str, float]]] = []
        self.measurement_current_line: list[dict[str, float]] = []
        self.measurement_line_payload: dict[str, Any] | None = None
        self.measurement_line_index = 0
        self.measurement_point_index = 0
        self.measurement_paused = False
        self._safe_close_in_progress = False
        self._safe_close_approved = False
        self._safe_close_wait_attempts = 0
        self._safe_close_progress: QProgressDialog | None = None
        self.system_connected = False
        self.system_busy = False
        self.connection_manager = ConnectionManager()
        self.console_logger = ConsoleLogger()
        self.console_logger.subscribe(lambda record: self.append_log(record.message))
        self.simulation_engine = SimulationEngine(self.console_logger)
        self.simulation_sample_type = "half_ball"
        self.simulation_sample_params = self.simulation_defaults(self.simulation_sample_type)
        self.simulation_config_dialog: SimulationConfigDialog | None = None
        self.simulation_menu_action: QAction | None = None

        root = QWidget()

        # PROFESSIONAL_INSTRUMENT_STYLE — Bruker/Park/Oxford scientific instrument palette
        # Light neutral background, charcoal text, colored status indicators only.
        root.setStyleSheet("""
            QWidget {
                font-family: Ubuntu, Inter, 'Segoe UI', Arial, sans-serif;
                font-size: 11px;
                color: #374151;
                background-color: #F5F6F8;
            }

            QMainWindow, QDialog {
                background-color: #F5F6F8;
            }

            QGroupBox {
                font-size: 11px;
                font-weight: 700;
                color: #1A1F2B;
                border: 1px solid #D0D5DD;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 8px;
                background-color: #FFFFFF;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 6px;
                color: #374151;
                background-color: #FFFFFF;
            }

            QPushButton {
                min-height: 28px;
                padding: 3px 10px;
                font-size: 11px;
                font-weight: 600;
                border-radius: 4px;
                border: 1px solid #D1D5DB;
                background-color: #F3F4F6;
                color: #374151;
            }
            QPushButton:hover {
                background-color: #E5E7EB;
            }
            QPushButton:pressed {
                background-color: #D1D5DB;
            }
            QPushButton:disabled {
                background-color: #F9FAFB;
                color: #9CA3AF;
                border-color: #E5E7EB;
            }

            QComboBox {
                min-height: 26px;
                padding: 2px 8px;
                font-size: 11px;
                border: 1px solid #D1D5DB;
                border-radius: 4px;
                background-color: #FFFFFF;
                color: #374151;
            }
            QComboBox:focus {
                border-color: #2563EB;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox QAbstractItemView {
                border: 1px solid #D1D5DB;
                background-color: #FFFFFF;
                selection-background-color: #EFF6FF;
                selection-color: #1D4ED8;
            }

            QLineEdit {
                min-height: 24px;
                padding: 2px 8px;
                font-size: 11px;
                border: 1px solid #D1D5DB;
                border-radius: 4px;
                background-color: #FFFFFF;
                color: #374151;
            }
            QLineEdit:focus {
                border-color: #2563EB;
            }

            QTextEdit {
                font-size: 11px;
                border: 1px solid #D1D5DB;
                border-radius: 4px;
                background-color: #FFFFFF;
                color: #374151;
            }
            QTextEdit:focus {
                border-color: #2563EB;
            }

            QCheckBox {
                font-size: 11px;
                color: #374151;
                spacing: 6px;
            }
            QCheckBox::indicator {
                width: 14px;
                height: 14px;
                border: 1px solid #D1D5DB;
                border-radius: 3px;
                background-color: #FFFFFF;
            }
            QCheckBox::indicator:checked {
                background-color: #2563EB;
                border-color: #2563EB;
            }

            QRadioButton {
                font-size: 11px;
                color: #374151;
                spacing: 6px;
            }
            QRadioButton::indicator {
                width: 14px;
                height: 14px;
                border: 1px solid #D1D5DB;
                border-radius: 7px;
                background-color: #FFFFFF;
            }
            QRadioButton::indicator:checked {
                background-color: #2563EB;
                border-color: #2563EB;
            }

            QTabWidget::pane {
                border: 1px solid #D0D5DD;
                border-radius: 0px 4px 4px 4px;
                background-color: #FFFFFF;
            }
            QTabBar::tab {
                font-size: 11px;
                font-weight: 600;
                padding: 6px 14px;
                border: 1px solid #D0D5DD;
                border-bottom: none;
                border-radius: 4px 4px 0 0;
                background-color: #F3F4F6;
                color: #6B7280;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #FFFFFF;
                color: #1A1F2B;
                border-color: #D0D5DD;
            }
            QTabBar::tab:hover:!selected {
                background-color: #E5E7EB;
            }

            QSplitter::handle {
                background-color: #E5E7EB;
                width: 3px;
                height: 3px;
            }
            QSplitter::handle:hover {
                background-color: #2563EB;
            }

            QScrollBar:vertical {
                border: none;
                background: #F3F4F6;
                width: 8px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background: #D1D5DB;
                border-radius: 4px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background: #9CA3AF;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }

            QSpinBox, QDoubleSpinBox {
                min-height: 24px;
                padding: 2px 6px;
                font-size: 11px;
                border: 1px solid #D1D5DB;
                border-radius: 4px;
                background-color: #FFFFFF;
                color: #374151;
            }
            QSpinBox:focus, QDoubleSpinBox:focus {
                border-color: #2563EB;
            }

            QLabel#sectionTitle {
                font-size: 13px;
                font-weight: 700;
                color: #1A1F2B;
            }

            QStatusBar {
                background-color: #1A1F2B;
                color: #D1D5DB;
                font-size: 11px;
                border-top: 1px solid #374151;
            }
            QStatusBar::item {
                border: none;
            }
        """)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Instrument Header Bar ──────────────────────────────────────────────
        # Always-visible strip: product identity + live telemetry + connection pill
        header_frame = QFrame()
        header_frame.setFrameShape(QFrame.Shape.NoFrame)
        header_frame.setStyleSheet(
            "QFrame { background-color: #1A1F2B; border-bottom: 1px solid #374151; }"
        )
        header_frame.setFixedHeight(56)
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(16, 6, 16, 6)
        header_layout.setSpacing(0)

        # Product identity
        product_label = QLabel("SPM Operator Workstation")
        product_label.setStyleSheet(
            "font-size: 14px; font-weight: 700; color: #F9FAFB; background: transparent;"
        )
        version_label = QLabel(f"  ·  {FULL_VERSION}  ·  {BUILD_DATE_DISPLAY}")
        version_label.setStyleSheet("font-size: 10px; color: #9CA3AF; background: transparent;")

        # Live telemetry labels (updated on every hardware poll)
        self.header_x = QLabel("X: —")
        self.header_y = QLabel("Y: —")
        self.header_z = QLabel("Z: —")
        self.header_temp = QLabel("T: —")
        for lbl in (self.header_x, self.header_y, self.header_z, self.header_temp):
            lbl.setStyleSheet(
                "font-size: 11px; font-weight: 600; color: #D1D5DB; background: transparent; padding: 0 8px;"
            )

        # Motion authorization pill
        self.header_auth_pill = QLabel("LOCKED")
        self.header_auth_pill.setStyleSheet(
            "font-size: 10px; font-weight: 700; color: #FEF3C7; background: #92400E;"
            "border-radius: 10px; padding: 2px 10px;"
        )

        # Connection status pill
        self.global_status_banner = QLabel("● OFFLINE")
        self.global_status_banner.setStyleSheet(
            "font-size: 10px; font-weight: 700; color: #FCA5A5; background: #7F1D1D;"
            "border-radius: 10px; padding: 2px 10px;"
        )

        header_layout.addWidget(product_label)
        header_layout.addWidget(version_label)
        header_layout.addStretch(1)
        header_layout.addWidget(QLabel(" ").setStyleSheet("") or QLabel(""))  # spacer
        for lbl in (self.header_x, self.header_y, self.header_z, self.header_temp):
            header_layout.addWidget(lbl)
        header_layout.addSpacing(12)
        header_layout.addWidget(self.header_auth_pill)
        header_layout.addSpacing(8)
        header_layout.addWidget(self.global_status_banner)

        layout.addWidget(header_frame)

        # ── Workspace ─────────────────────────────────────────────────────────
        workspace_widget = QWidget()
        workspace_widget.setStyleSheet("background-color: #F5F6F8;")
        workspace_layout = QHBoxLayout(workspace_widget)
        workspace_layout.setContentsMargins(8, 8, 8, 8)
        workspace_layout.setSpacing(0)

        # Build panels
        system_panel = self.build_system_panel()
        system_panel.setMinimumWidth(380)
        system_panel.setMaximumWidth(460)

        overview_panel = self.build_overview_panel()
        self.main_log_panel = self.build_main_log_panel()

        self.z_scanner_window = ZScannerWindow(self)
        self.live_log_window = LiveLogWindow(self)
        self.academic_gcode_window = AcademicGCodeWindow(self)
        self.crtouch_prep_window = CRTouchPrepWindow(self)

        # Embed all as widgets (no floating windows)
        self.z_scanner_window.setWindowFlags(Qt.WindowType.Widget)
        self.live_log_window.setWindowFlags(Qt.WindowType.Widget)
        self.academic_gcode_window.setWindowFlags(Qt.WindowType.Widget)
        self.crtouch_prep_window.setWindowFlags(Qt.WindowType.Widget)

        # Center tabbed workspace
        self.center_tabs = QTabWidget()
        self.center_tabs.addTab(self.z_scanner_window, "🔬 Scan & Metrology")
        self.center_tabs.addTab(overview_panel, "📋 System Overview")
        self.center_tabs.addTab(self.crtouch_prep_window, "🔧 Probe Diagnostics")
        self.center_tabs.addTab(self.academic_gcode_window, "⚡ Academic G-Code")

        # AI Advisor + Log right panel
        right_panel = self.build_ai_advisor_panel()

        workspace_splitter = QSplitter(Qt.Orientation.Horizontal)
        workspace_splitter.addWidget(system_panel)
        workspace_splitter.addWidget(self.center_tabs)
        workspace_splitter.addWidget(right_panel)
        workspace_splitter.setStretchFactor(0, 0)
        workspace_splitter.setStretchFactor(1, 1)
        workspace_splitter.setStretchFactor(2, 0)
        workspace_splitter.setSizes([420, 1400, 520])
        workspace_layout.addWidget(workspace_splitter)

        layout.addWidget(workspace_widget, 1)

        root.setLayout(layout)
        self.setCentralWidget(root)
        self.build_menu_bar()

        # ── Status Bar ────────────────────────────────────────────────────────
        self._status_bar = self.statusBar()
        self._status_bar.showMessage("Instrument ready — connect hardware or use simulation mode")

        self.append_log(f"{APP_TITLE} loaded. Simulation is available offline; hardware motion remains locked.")
        self.load_z_reference()
        self.update_scan_summary()
        self.update_system_connection_controls(connected=False, busy=False)
        self.apply_motion_authorization("LOCKED", confirm=False)

    def build_ai_advisor_panel(self) -> QWidget:
        """Right panel: AI Advisor (top) + Session Log (bottom).

        The AI Advisor surfaces the existing ``build_ai_recommendation()`` backend
        as a persistent instrument assistant. Hardware context (position, temperature,
        motion state, last error) is auto-injected into every query so the LLM has
        full situational awareness. The panel degrades gracefully when Ollama is
        offline, showing deterministic fallback recommendations.
        """
        container = QWidget()
        container.setMinimumWidth(300)
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        splitter = QSplitter(Qt.Orientation.Vertical)

        # ── Autonomous AI Copilot Section (Futuristic Cyber-Scientific HUD) ─
        advisor_widget = QGroupBox("Autonomous AI Copilot")
        advisor_widget.setStyleSheet(
            "QGroupBox { font-size: 11px; font-weight: 800; color: #00F0FF; "
            "border: 1px solid #1E3A5F; border-radius: 6px; margin-top: 10px; "
            "padding-top: 10px; background-color: #0B111E; }"
            "QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 6px; "
            "color: #00F0FF; background-color: #0B111E; }"
        )
        advisor_layout = QVBoxLayout(advisor_widget)
        advisor_layout.setContentsMargins(10, 14, 10, 10)
        advisor_layout.setSpacing(8)

        # Copilot Status & HUD Indicator
        ai_status_row = QHBoxLayout()
        self.ai_model_pill = QLabel("● AUTONOMOUS COPILOT ACTIVE")
        self.ai_model_pill.setStyleSheet(
            "font-size: 10px; font-weight: 700; color: #00FF9D; background: #06231A; "
            "border: 1px solid #00FF9D; border-radius: 4px; padding: 3px 8px;"
        )
        mode_badge = QLabel("AGENTIC SPM CORE")
        mode_badge.setStyleSheet(
            "font-size: 9px; font-weight: 700; color: #94A3B8; background: #162032; "
            "border-radius: 4px; padding: 3px 6px;"
        )
        ai_status_row.addWidget(self.ai_model_pill)
        ai_status_row.addStretch(1)
        ai_status_row.addWidget(mode_badge)
        advisor_layout.addLayout(ai_status_row)

        # Quick Action Chips (Futuristic 1-Click Buttons)
        chip_row = QHBoxLayout()
        chip_row.setSpacing(4)
        chip_sample = QPushButton("🎯 Sample 2.0mm")
        chip_connect = QPushButton("🔌 Auto-Port")
        chip_correct = QPushButton("🩺 Self-Correct")
        chip_metrology = QPushButton("🔬 ISO Metrology")
        for chip in (chip_sample, chip_connect, chip_correct, chip_metrology):
            chip.setStyleSheet(
                "QPushButton { font-size: 10px; font-weight: 700; color: #93C5FD; "
                "background: #111C30; border: 1px solid #1D4ED8; border-radius: 4px; padding: 4px 6px; }"
                "QPushButton:hover { background: #1D4ED8; color: #FFFFFF; border-color: #3B82F6; }"
            )
        chip_sample.clicked.connect(lambda: self._send_ai_advisor_message_with_text(
            "I have a sample on the surface, the height is 2.0mm, configure scan 10x10mm"
        ))
        chip_connect.clicked.connect(lambda: self._send_ai_advisor_message_with_text(
            "Find the right port and connect to device"
        ))
        chip_correct.clicked.connect(lambda: self._send_ai_advisor_message_with_text(
            "Self-correct connection issues and verify safety interlocks"
        ))
        chip_metrology.clicked.connect(lambda: self._send_ai_advisor_message_with_text(
            "Analyze current surface topography and calculate ISO 25178 roughness"
        ))
        chip_row.addWidget(chip_sample)
        chip_row.addWidget(chip_connect)
        chip_row.addWidget(chip_correct)
        chip_row.addWidget(chip_metrology)
        advisor_layout.addLayout(chip_row)

        # Chat Transcript (Futuristic Cyber HUD Console)
        self.ai_chat_transcript = QTextEdit()
        self.ai_chat_transcript.setReadOnly(True)
        self.ai_chat_transcript.setPlaceholderText(
            "⚡ AUTONOMOUS SPM COPILOT READY\n\n"
            "Tell me your intent in plain language, for example:\n"
            "• 'I have a sample on the surface the height is 2.5mm'\n"
            "• 'Find the right port and connect'\n"
            "• 'Self-correct connection issues'\n"
            "• 'Analyze the surface topography'\n\n"
            "I automatically configure parameters, diagnose hardware, and generate multi-step workflows."
        )
        self.ai_chat_transcript.setStyleSheet(
            "QTextEdit { background: #060A12; border: 1px solid #1E293B; "
            "border-radius: 4px; font-size: 11px; color: #E2E8F0; font-family: 'Consolas', monospace; }"
        )
        advisor_layout.addWidget(self.ai_chat_transcript, 1)

        # Autonomous Workflow Execution Button
        self.ai_execute_plan_btn = QPushButton("⚡ Execute Autonomous Workflow")
        self.ai_execute_plan_btn.setEnabled(False)
        self.ai_execute_plan_btn.setMinimumHeight(38)
        self.ai_execute_plan_btn.setStyleSheet(
            "QPushButton { font-size: 11px; font-weight: 800; color: #060A12; "
            "background: #00FF9D; border: 1px solid #00FF9D; border-radius: 4px; padding: 6px; }"
            "QPushButton:hover { background: #00E58D; }"
            "QPushButton:disabled { background: #1E293B; color: #64748B; border-color: #334155; }"
        )
        self.ai_execute_plan_btn.clicked.connect(self._run_current_autonomous_plan)
        advisor_layout.addWidget(self.ai_execute_plan_btn)

        # Input field
        self.ai_input = QLineEdit()
        self.ai_input.setPlaceholderText("Command Copilot: e.g. 'I have a sample on the surface the height is 1.8mm'...")
        self.ai_input.setStyleSheet(
            "QLineEdit { background: #060A12; border: 1px solid #1E3A5F; border-radius: 4px; "
            "color: #F8FAFC; font-size: 11px; padding: 6px 10px; }"
            "QLineEdit:focus { border-color: #00F0FF; }"
        )
        self.ai_input.returnPressed.connect(self._send_ai_advisor_message)
        advisor_layout.addWidget(self.ai_input)

        # Action buttons
        ask_row = QHBoxLayout()
        ask_btn = QPushButton("Send to Copilot")
        ask_btn.setStyleSheet(
            "QPushButton { background: #2563EB; color: white; font-weight: 700; padding: 6px 12px; border-radius: 4px; }"
            "QPushButton:hover { background: #1D4ED8; }"
        )
        ask_btn.clicked.connect(self._send_ai_advisor_message)
        context_btn = QPushButton("Telemetry")
        context_btn.setToolTip("Inject live hardware telemetry into Copilot reasoning.")
        context_btn.setStyleSheet(GRAY_BUTTON_STYLE)
        context_btn.clicked.connect(self._send_ai_hardware_context)
        clear_btn = QPushButton("Clear")
        clear_btn.setStyleSheet(GRAY_BUTTON_STYLE)
        clear_btn.clicked.connect(self.ai_chat_transcript.clear)
        ask_row.addWidget(ask_btn, 2)
        ask_row.addWidget(context_btn, 1)
        ask_row.addWidget(clear_btn, 1)
        advisor_layout.addLayout(ask_row)

        splitter.addWidget(advisor_widget)

        # ── Session Log section ───────────────────────────────────────────────
        log_widget = QGroupBox("Session Log")
        log_layout = QVBoxLayout(log_widget)
        log_layout.setContentsMargins(8, 12, 8, 8)
        log_layout.setSpacing(4)
        log_layout.addWidget(self.build_log_panel())
        splitter.addWidget(log_widget)

        splitter.setSizes([450, 250])
        container_layout.addWidget(splitter)

        self._autonomous_agent = AutonomousSPMAgent(self)
        self._current_autonomous_plan: list[Any] = []

        # Async model status check (non-blocking)
        QTimer.singleShot(1200, self._refresh_ai_model_status)

        return container

    def _refresh_ai_model_status(self) -> None:
        """Non-blocking check of local AI model availability."""
        try:
            from core.ai.academic_ai_client import get_local_ai_status
            status = get_local_ai_status()
            model = status.get("model", "?")
            configured = bool(status.get("configured"))
            if configured:
                self.ai_model_pill.setText(f"● COPILOT ACTIVE [{model}]")
                self.ai_model_pill.setStyleSheet(
                    "font-size: 10px; font-weight: 700; color: #00FF9D; background: #06231A;"
                    "border: 1px solid #00FF9D; border-radius: 4px; padding: 3px 8px;"
                )
            else:
                self.ai_model_pill.setText("● COPILOT ACTIVE [DETERMINISTIC]")
                self.ai_model_pill.setStyleSheet(
                    "font-size: 10px; font-weight: 700; color: #00F0FF; background: #071E26;"
                    "border: 1px solid #00F0FF; border-radius: 4px; padding: 3px 8px;"
                )
        except Exception:
            self.ai_model_pill.setText("● COPILOT OFFLINE")
            self.ai_model_pill.setStyleSheet(
                "font-size: 10px; font-weight: 700; color: #EF4444; background: #260B0B;"
                "border: 1px solid #EF4444; border-radius: 4px; padding: 3px 8px;"
            )

    def _collect_hardware_context(self) -> dict[str, Any]:
        """Assemble current instrument state for AI context injection."""
        return {
            "system_connected": bool(self.system_connected),
            "motion_authorization": str(getattr(self, "motion_authorization", "LOCKED")),
            "latest_z_mm": float(self.latest_z_value),
            "last_system_payload": dict(self.last_system_payload),
            "simulation_active": bool(self.simulation_engine.is_active),
            "acquisition_mode": (
                self.z_scanner_window.acquisition_mode.currentText()
                if self.z_scanner_window is not None else "Unknown"
            ),
        }

    def _send_ai_advisor_message(self) -> None:
        """Send user prompt to Autonomous SPM Agent and display rich response."""
        question = self.ai_input.text().strip()
        if not question:
            return
        self.ai_input.clear()
        self.ai_chat_transcript.append(f"<span style='color:#00F0FF;'><b>Operator &gt;</b> {question}</span>")
        context = self._collect_hardware_context()

        # Check if operator said 'execute' or 'proceed'
        if question.lower() in ("execute", "proceed", "run plan", "start plan", "go"):
            if self._current_autonomous_plan:
                self._run_current_autonomous_plan()
                return

        # Execute Autonomous Agent interpretation
        agent = getattr(self, "_autonomous_agent", None) or AutonomousSPMAgent(self)
        self._autonomous_agent = agent
        response = agent.interpret_user_command(question, context)

        # Render response in cyber console
        self.ai_chat_transcript.append(
            f"<div style='margin: 6px 0; padding: 8px; background: #0E1626; border-left: 3px solid #00F0FF; "
            f"border-radius: 4px; font-family: monospace;'>"
            f"{response.natural_response.replace(chr(10), '<br>')}"
            f"</div>"
        )

        # If a multi-step plan was generated, load it and update execute button
        if response.plan:
            self._current_autonomous_plan = response.plan
            self.ai_execute_plan_btn.setEnabled(True)
            self.ai_execute_plan_btn.setText(f"⚡ Execute Autonomous Workflow ({len(response.plan)} Steps)")
            self.append_log(f"[AI AGENT] Generated autonomous workflow with {len(response.plan)} steps.")
        else:
            self.ai_execute_plan_btn.setEnabled(False)
            self.ai_execute_plan_btn.setText("⚡ Execute Autonomous Workflow")

        self.ai_chat_transcript.verticalScrollBar().setValue(
            self.ai_chat_transcript.verticalScrollBar().maximum()
        )

    def _run_current_autonomous_plan(self) -> None:
        """Safely step through the active autonomous plan."""
        if not self._current_autonomous_plan:
            return
        self.ai_execute_plan_btn.setEnabled(False)
        self.ai_chat_transcript.append("<span style='color:#00FF9D;'><b>[AGENT] Executing Autonomous Workflow...</b></span>")
        agent = getattr(self, "_autonomous_agent", None) or AutonomousSPMAgent(self)

        completed_count = 0
        for step in self._current_autonomous_plan:
            self.ai_chat_transcript.append(f"<span style='color:#94A3B8;'>• Step: {step.title}...</span>")
            success = agent.execute_plan_step(step)
            if success:
                completed_count += 1
                self.ai_chat_transcript.append(f"<span style='color:#00FF9D;'>  ✓ {step.result_message or 'Done.'}</span>")
            else:
                self.ai_chat_transcript.append(f"<span style='color:#EF4444;'>  ✗ Error: {step.result_message}</span>")
                break

        self.ai_chat_transcript.append(
            f"<span style='color:#00FF9D;'><b>[AGENT] Workflow Completed: {completed_count}/{len(self._current_autonomous_plan)} steps executed.</b></span><br>"
        )
        self.ai_execute_plan_btn.setText("⚡ Autonomous Workflow Complete")
        self.ai_chat_transcript.verticalScrollBar().setValue(
            self.ai_chat_transcript.verticalScrollBar().maximum()
        )

    def _send_ai_hardware_context(self) -> None:
        """Inject current hardware state into AI for situational analysis."""
        self._send_ai_advisor_message_with_text(
            "Analyze the current instrument state and advise on next steps."
        )

    def _send_ai_advisor_message_with_text(self, text: str) -> None:
        self.ai_input.setText(text)
        self._send_ai_advisor_message()

    def build_header(self) -> QVBoxLayout:
        header = QVBoxLayout()
        header.setSpacing(8)

        top = QHBoxLayout()
        title = QLabel(
            "<b>SPM Operator</b><br>"
            "<span style='color:#94a3b8'>Connect to MK4S, prepare, and start SPM measurements</span>"
        )
        handbook_button = QPushButton("📖  Project Handbook")
        handbook_button.setToolTip(
            "Open the local construction, wiring, commissioning, and operating handbook"
        )
        handbook_button.setStyleSheet(
            "QPushButton { background:#0f766e; color:white; font-weight:800; "
            "padding:6px 10px; border:1px solid #0b5f59; border-radius:4px; } "
            "QPushButton:hover { background:#115e59; }"
        )
        handbook_button.clicked.connect(self.open_project_handbook)

        top.addWidget(title)
        top.addStretch(1)
        top.addWidget(handbook_button)

        controls = QHBoxLayout()

        repeat_scan_button = QPushButton("Discover & Refine Objects")
        repeat_scan_button.setToolTip(
            "Survey the full field, discover separated raised objects, then refine each region"
        )
        repeat_scan_button.setStyleSheet(
            "QPushButton { background:#1d4ed8; color:white; font-weight:800; "
            "padding:6px 10px; border:1px solid #1e40af; border-radius:4px; } "
            "QPushButton:hover { background:#1e40af; }"
        )
        repeat_scan_button.clicked.connect(self.start_two_object_adaptive_scan)
        self.repeat_two_object_button = repeat_scan_button

        self.two_object_resolution = QComboBox()
        self.two_object_resolution.addItem(
            "Balanced · 20 mm overview → 5 mm focus", "quick"
        )
        self.two_object_resolution.addItem(
            "Precision · 20 mm overview → 2.5 mm focus", "high"
        )
        self.two_object_resolution.addItem(
            "Research · 15 mm overview → 1 mm focus", "research"
        )
        self.two_object_resolution.setMinimumWidth(250)
        self.two_object_resolution.setToolTip(
            "Balanced is the validated default. Precision and Research are "
            "progressively slower focused refinements."
        )

        try:
            active_mount = load_mount_profiles(PROJECT_ROOT)
            mount_text = str(
                active_mount["profile"].get("display_name", active_mount["name"])
            )
        except Exception:
            mount_text = "Mount profile unreadable"

        self.mount_profile_label = QLabel(f"Probe: {mount_text}")
        self.mount_profile_label.setToolTip(
            "Mechanical profile is fail-closed in config/crtouch_mount_profiles.json"
        )

        self.profile_select = QComboBox()
        self.profile_select.addItems(["Student", "Instructor"])
        self.profile_select.setCurrentText(
            str(self.settings.value("ui/profile", "Student"))
        )
        self.profile_select.currentTextChanged.connect(
            lambda value: self.settings.setValue("ui/profile", value)
        )
        self.profile_select.currentTextChanged.connect(
            lambda _value: self.update_run_controls()
        )

        controls.addWidget(self.mount_profile_label)
        controls.addStretch(1)
        controls.addWidget(self.two_object_resolution)
        controls.addWidget(repeat_scan_button)
        controls.addWidget(QLabel("Profile:"))
        controls.addWidget(self.profile_select)

        header.addLayout(top)
        header.addLayout(controls)
        return header

    def open_project_handbook(self) -> None:
        """Open the read-only local project handbook without changing hardware state."""

        launcher = PROJECT_ROOT / "web" / "project_handbook" / "OPEN_HANDBOOK.ps1"
        offline_index = PROJECT_ROOT / "web" / "project_handbook" / "index.html"
        try:
            if launcher.is_file():
                creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
                subprocess.Popen(
                    [
                        "powershell.exe",
                        "-NoProfile",
                        "-ExecutionPolicy",
                        "Bypass",
                        "-File",
                        str(launcher),
                    ],
                    cwd=str(launcher.parent),
                    creationflags=creation_flags,
                )
                self.append_log("[HANDBOOK] Opening the local construction handbook.")
                return
            if offline_index.is_file():
                os.startfile(str(offline_index))
                self.append_log("[HANDBOOK] Opened the offline handbook index.")
                return
            raise FileNotFoundError("The handbook launcher and offline index are missing.")
        except Exception as exc:
            QMessageBox.warning(
                self,
                "Handbook Could Not Open",
                f"The local handbook could not be opened.\n\n{exc}\n\n"
                f"Expected location:\n{offline_index}",
            )

    @staticmethod
    def simulation_sample_label(sample_type: str) -> str:
        return {
            "half_ball": "Half Ball", "square": "Square Mesa", "bravais_111": "Bravais (111)",
            "bravais_100": "Bravais (100)", "bravais_110": "Bravais (110)",
        }[sample_type]

    @staticmethod
    def simulation_sample_key(label: str) -> str:
        normalized = str(label).strip().lower()
        return {
            "half ball": "half_ball", "square mesa": "square", "bravais (111)": "bravais_111",
            "bravais (100)": "bravais_100", "bravais (110)": "bravais_110",
        }.get(normalized, normalized)

    @staticmethod
    def simulation_parameter_keys(sample_type: str) -> tuple[str, ...]:
        common = ("height", "rotation", "center_x", "center_y")
        return {
            "half_ball": ("radius", "height", "center_x", "center_y"),
            "square": ("width", "height", "edge_sharpness", "center_x", "center_y"),
            "bravais_111": ("lattice_constant", *common),
            "bravais_100": ("lattice_constant", *common),
            "bravais_110": ("lattice_constant_a", "lattice_constant_b", *common),
        }[sample_type]

    @staticmethod
    def simulation_defaults(sample_type: str) -> dict[str, float]:
        center = {"center_x": 125.0, "center_y": 105.0}
        return {
            "half_ball": {**center, "radius": 10.0, "height": 2.0},
            "square": {**center, "width": 12.0, "height": 1.0, "edge_sharpness": 0.5},
            "bravais_111": {**center, "lattice_constant": 2.0, "height": 0.25, "rotation": 0.0},
            "bravais_100": {**center, "lattice_constant": 2.0, "height": 0.25, "rotation": 0.0},
            "bravais_110": {**center, "lattice_constant_a": 2.0, "lattice_constant_b": 3.5, "height": 0.25, "rotation": 0.0},
        }[sample_type]

    def set_simulation_enabled(self, enabled: bool) -> None:
        enabled = bool(enabled)
        if enabled:
            self.simulation_engine.enable(self.simulation_sample_type, self.simulation_sample_params)
        else:
            self.simulation_engine.disable()
        if self.z_scanner_window is not None:
            self.z_scanner_window.simulation_badge.setVisible(enabled)
            target_mode = "Simulation" if enabled else "Real Scan"
            self.z_scanner_window.acquisition_mode.blockSignals(True)
            self.z_scanner_window.acquisition_mode.setCurrentText(target_mode)
            self.z_scanner_window.acquisition_mode.blockSignals(False)
            self.z_scanner_window.simulation_toggle.blockSignals(True)
            self.z_scanner_window.simulation_toggle.setChecked(enabled)
            self.z_scanner_window.simulation_toggle.blockSignals(False)
            self.z_scanner_window.update_instrument_state(
                connected=self.system_connected,
                motion_enabled=False if enabled else os.getenv("SPM_WEB_ALLOW_REAL_SCAN", "0") == "1",
                acquisition="Simulation Ready" if enabled else "Hardware Idle",
            )
        if self.simulation_menu_action is not None and self.simulation_menu_action.isChecked() != enabled:
            self.simulation_menu_action.blockSignals(True)
            self.simulation_menu_action.setChecked(enabled)
            self.simulation_menu_action.blockSignals(False)
        if hasattr(self, "authorization_select"):
            self.update_authorization_controls()

    def set_acquisition_mode(self, mode: str) -> None:
        """Apply the operator's explicit simulation, safe dry-run, or real-scan choice."""
        mode = str(mode)
        simulation_enabled = mode in {"Simulation", "Dry Run"}
        if simulation_enabled:
            self.simulation_engine.enable(self.simulation_sample_type, self.simulation_sample_params)
        else:
            self.simulation_engine.disable()
        if self.z_scanner_window is not None:
            self.z_scanner_window.simulation_toggle.blockSignals(True)
            self.z_scanner_window.simulation_toggle.setChecked(simulation_enabled)
            self.z_scanner_window.simulation_toggle.blockSignals(False)
            self.z_scanner_window.simulation_badge.setVisible(simulation_enabled)
            messages = {
                "Simulation": "Simulation selected — software-only movement and generated feedback; no hardware commands.",
                "Dry Run": "DRY RUN — complete virtual scan and simulated probe feedback; no MK4S motion, G-code, or CR-Touch is required.",
                "Real Scan": "REAL SCAN — connect the MK4S, install the physical sample, and select OPERATIONAL.",
            }
            self.z_scanner_window.session_message.setText(messages.get(mode, "Unknown acquisition mode."))
        self.append_log(f"[ACQUISITION MODE] Operator selected {mode}.")

    def select_simulation_sample(self, label: str) -> None:
        sample_type = self.simulation_sample_key(label)
        if sample_type == self.simulation_sample_type:
            return
        self.simulation_sample_type = sample_type
        self.simulation_sample_params = self.simulation_defaults(sample_type)
        if self.simulation_engine.is_active:
            self.simulation_engine.enable(sample_type, self.simulation_sample_params)

    def apply_simulation_configuration(self, sample_type: str, params: dict[str, float]) -> None:
        self.simulation_sample_type = sample_type
        self.simulation_sample_params = dict(params)
        self.simulation_engine.enable(sample_type, params)
        if self.z_scanner_window is not None:
            self.z_scanner_window.simulation_toggle.setChecked(True)
            self.z_scanner_window.simulation_sample.blockSignals(True)
            self.z_scanner_window.simulation_sample.setCurrentText(self.simulation_sample_label(sample_type))
            self.z_scanner_window.simulation_sample.blockSignals(False)
            self.z_scanner_window.session_message.setText(
                f"Virtual sample applied: {self.simulation_sample_label(sample_type)}. No hardware commands will be sent."
            )

    def open_simulation_configuration(self) -> None:
        self.simulation_config_dialog = SimulationConfigDialog(self)
        self.simulation_config_dialog.show()
        self.simulation_config_dialog.raise_()

    def build_overview_panel(self) -> QGroupBox:
        box = QGroupBox("System Overview")
        layout = QVBoxLayout()
        intro = QLabel(
            "General control and safety status are kept here. Z control, scan setup, XY measurement, "
            "live line data, and topography are organized in the dedicated Scan Control workspace."
        )
        intro.setWordWrap(True)
        intro.setStyleSheet("font-size:14px; color:#1f2937; padding:12px; background:#f8fbff; border:1px solid #8da2b8;")
        authorization_group = QGroupBox("Motion Authorization")
        authorization_layout = QHBoxLayout()
        self.authorization_select = QComboBox()
        self.authorization_select.addItems(["LOCKED", "STANDBY", "OPERATIONAL"])
        self.authorization_select.setToolTip(
            "LOCKED: no motion. STANDBY: Z/park preparation only. OPERATIONAL: Z and XY scan motion."
        )
        self.authorization_select.currentTextChanged.connect(self.apply_motion_authorization)
        authorization_layout.addWidget(QLabel("Authorization Level"))
        authorization_layout.addWidget(self.authorization_select, 1)
        authorization_group.setLayout(authorization_layout)
        open_scan = QPushButton("LAUNCH SCAN WORKSPACE")
        open_scan.setMinimumHeight(48)
        open_scan.setStyleSheet(GREEN_BUTTON_STYLE)
        open_scan.setToolTip("Open the Z approach, feedback, XY raster, and data acquisition workspace.")
        open_scan.clicked.connect(self.open_z_scanner_window)
        self.open_scan_button = open_scan
        teaching_badge = QLabel("TEACHING MODE · CRTouch EMULATION")
        teaching_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        teaching_badge.setStyleSheet("color:#f5d66f; background:#343434; border-radius:8px; padding:6px;")
        self.overview_status = QLabel("Status: Disconnected\nMode: Read-only safety default\nMotion authorization: Disabled")
        self.overview_status.setWordWrap(True)
        self.overview_status.setStyleSheet("color:#1f2937; padding:12px; border:1px solid #8da2b8; background:#f8fbff;")
        note = QLabel("Motion remains opt-in. Opening Scan Control does not authorize or execute movement.")
        note.setWordWrap(True)
        note.setStyleSheet("color:#704d00; background:#fff8df; border:1px solid #d9a400; padding:10px;")
        layout.addWidget(intro)
        layout.addWidget(authorization_group)
        layout.addWidget(open_scan)
        layout.addWidget(teaching_badge)
        layout.addWidget(self.overview_status)
        layout.addWidget(note)
        layout.addStretch(1)
        box.setLayout(layout)
        return box

    def apply_motion_authorization(self, level: str, confirm: bool = True) -> None:
        level = str(level).upper()
        if level == "OPERATIONAL" and confirm:
            answer = QMessageBox.warning(
                self,
                "Authorize Full Motion",
                "OPERATIONAL enables real Z and XY movement, scanning, and tapping.\n\n"
                "Verify probe clearance, sample mounting, limits, and emergency-stop access. Continue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                self.authorization_select.blockSignals(True)
                self.authorization_select.setCurrentText(self.motion_authorization)
                self.authorization_select.blockSignals(False)
                return
        self.motion_authorization = level
        gates = {
            "LOCKED": ("0", "0", "0", "0"),
            "STANDBY": ("1", "1", "0", "0"),
            "OPERATIONAL": ("1", "1", "1", "1"),
        }.get(level, ("0", "0", "0", "0"))
        os.environ["SPM_WEB_ALLOW_HEALTH_MOTION"] = gates[0]
        os.environ["SPM_WEB_ALLOW_Z_MOTION"] = gates[1]
        os.environ["SPM_WEB_ALLOW_REAL_SCAN"] = gates[2]
        os.environ["SPM_WEB_ALLOW_FOIL_TAP"] = gates[3]
        self.append_log(f"[SAFETY] Motion authorization changed to {level} by profile {self.profile_select.currentText()}.")

        # Update header auth pill with authorization-appropriate color
        if hasattr(self, "header_auth_pill"):
            pill_styles = {
                "LOCKED": ("LOCKED", "#FEF3C7", "#92400E"),       # amber — restricted
                "STANDBY": ("STANDBY", "#FEF3C7", "#1E40AF"),     # blue — Z authorized
                "OPERATIONAL": ("OPERATIONAL", "#DCFCE7", "#166534"),  # green — full motion
            }
            label, fg, bg = pill_styles.get(level, ("LOCKED", "#FEF3C7", "#92400E"))
            self.header_auth_pill.setText(label)
            self.header_auth_pill.setStyleSheet(
                f"font-size: 10px; font-weight: 700; color: {fg}; background: {bg};"
                "border-radius: 10px; padding: 2px 10px;"
            )

        # Update status bar
        if hasattr(self, "_status_bar") and self.system_connected:
            self._status_bar.showMessage(f"Connected · Motion: {level} · Safety gate ARMED")

        self.update_authorization_controls()

    def update_authorization_controls(self) -> None:
        connected = bool(self.system_connected)
        busy = bool(self.system_busy)

        standby = (
            connected
            and self.motion_authorization in {"STANDBY", "OPERATIONAL"}
        )
        operational = (
            connected
            and self.motion_authorization == "OPERATIONAL"
        )

        # READ-ONLY CONTROL CLASS
        if hasattr(self, "readonly_buttons"):
            for button in self.readonly_buttons:
                button.setEnabled(connected and not busy)
                if connected:
                    button.setToolTip(
                        "Read-only hardware query. No movement commands."
                    )
                else:
                    button.setToolTip(
                        "Connect to the MK4S read-only interface first."
                    )

        # MOTION CONTROL CLASS
        if hasattr(self, "motion_buttons"):
            for button in self.motion_buttons:
                button.setEnabled(standby and not busy)
                if standby:
                    button.setToolTip(
                        "Controlled hardware action permitted by current "
                        "authorization."
                    )
                else:
                    button.setToolTip(
                        "Requires MK4S connection and STANDBY or "
                        "OPERATIONAL authorization."
                    )

        # Advisory / discovery controls never authorize motion.
        if hasattr(self, "ai_fix_button"):
            self.ai_fix_button.setEnabled(not busy)
            self.ai_fix_button.setToolTip(
                "Advisory analysis only. Cannot authorize or execute motion."
            )

        if hasattr(self, "refresh_button"):
            self.refresh_button.setEnabled(not busy)

        if hasattr(self, "open_scan_button"):
            self.open_scan_button.setEnabled(True)
            self.open_scan_button.setToolTip(
                "Open Scan Control. Simulation works offline; "
                "real acquisition requires authorization."
            )

        if self.z_scanner_window is not None:
            self.z_scanner_window.set_motion_interlocks(
                connected=connected,
                standby=standby,
                operational=operational,
            )

    def build_main_log_panel(self) -> QGroupBox:
        box = QGroupBox("Logs")
        layout = QVBoxLayout()
        controls = QHBoxLayout()
        self.log_search = QLineEdit()
        self.log_search.setPlaceholderText("Search logs")
        self.log_search.returnPressed.connect(lambda: self.main_log.find(self.log_search.text()))
        copy_button = QPushButton("Copy")
        save_button = QPushButton("Save Log…")
        clear_button = QPushButton("Clear")
        self.auto_scroll = QCheckBox("Auto-scroll")
        self.auto_scroll.setChecked(True)
        self.show_timestamps = QCheckBox("Timestamps")
        self.show_timestamps.setChecked(True)
        copy_button.clicked.connect(lambda: QApplication.clipboard().setText(self.main_log.toPlainText()))
        save_button.clicked.connect(self.download_log)
        clear_button.clicked.connect(self.clear_log)
        controls.addWidget(self.log_search, 1)
        for widget in (copy_button, save_button, clear_button, self.show_timestamps, self.auto_scroll):
            controls.addWidget(widget)
        layout.addLayout(controls)
        tabs = QTabWidget()
        self.main_log = QTextEdit()
        self.main_log.setReadOnly(True)
        self.main_log.setPlainText(f"{APP_TITLE} ready. Connect hardware or open Scan Control for simulation.")
        tabs.addTab(self.main_log, "Console")
        self.severity_logs = {}
        for name in ("Events", "Warnings", "Errors"):
            area = QTextEdit()
            area.setReadOnly(True)
            tabs.addTab(area, name)
            self.severity_logs[name.lower()] = area
        layout.addWidget(tabs)
        box.setLayout(layout)
        box.setMinimumHeight(200)
        box.setMaximumHeight(320)
        return box

    def update_scan_summary(self) -> None:
        if self.measurement_window is None:
            return
        window = self.measurement_window
        mode = "Tapping" if window.tapping_mode.isChecked() else "Constant-height"
        summary = (
            f"Mode: {mode} training scan\nResolution: {window.resolution.value()} × {window.resolution.value()}\n"
            f"Scan Size: {window.x_size.value():.1f} × {window.y_size.value():.1f} mm\n"
            f"Rotation: {window.rotation.value():.1f}° · Speed: {window.scan_speed.value():.1f} mm/s\n"
            "Probe: CRTouch · Tip status: verify before scan"
        )
        if hasattr(self, "scan_summary"):
            self.scan_summary.setText(summary)
        if self.z_scanner_window is not None:
            self.z_scanner_window.xy_summary.setText(summary)

    def update_run_controls(self) -> None:
        if not hasattr(self, "quick_checks"):
            return
        checklist_ready = all(check.isChecked() for check in self.quick_checks)
        student_ready = checklist_ready or self.profile_select.currentText() == "Instructor"
        ready = self.system_connected and student_ready
        self.start_scan_button.setEnabled(ready)
        self.run_warning.setText(
            "Ready to start with the validated Scan Control parameters." if ready
            else "Connect to MK4S and complete the checklist before starting."
        )

    def start_scan_from_main(self) -> None:
        if self.measurement_window is None or self.z_scanner_window is None:
            return
        if not self.z_scanner_window.apply_inline_scan_parameters():
            return
        mode = self.choose_scan_acquisition_mode()
        if mode is None:
            self.append_log("[SCAN] Start cancelled before an acquisition mode was selected.")
            return
        self.z_scanner_window.acquisition_mode.setCurrentText(mode)
        profile = self.measurement_window.profile()
        speed = self.measurement_window.scan_speed.value()
        self.z_scanner_window.update_instrument_state(
            connected=self.system_connected,
            motion_enabled=os.getenv("SPM_WEB_ALLOW_REAL_SCAN", "0") == "1",
            acquisition=f"Starting {mode}",
        )
        if mode == "Simulation":
            self.start_measurement_simulation(profile, speed, dry_run=False)
            return
        if mode == "Dry Run":
            self.start_measurement_simulation(profile, speed, dry_run=True)
            return
        if self.motion_authorization != "OPERATIONAL":
            QMessageBox.warning(self, "Hardware Scan Locked", "Select OPERATIONAL authorization before starting hardware acquisition.")
            return
        self.measurement_window.start_selected_mode()

    def choose_scan_acquisition_mode(self) -> str | None:
        dialog = QMessageBox(self)
        dialog.setWindowTitle("Choose Scan Acquisition")
        dialog.setIcon(QMessageBox.Icon.Question)
        dialog.setText("How should this scan run?")
        dialog.setInformativeText(
            "Simulation explores generated signals. Dry Run exercises the complete scan workflow with a virtual sample "
            "and simulated probe feedback; it sends no G-code and needs no CR-Touch. Real Measurement moves hardware "
            "over a physical sample and requires OPERATIONAL authorization."
        )
        simulation = dialog.addButton("Simulation", QMessageBox.ButtonRole.ActionRole)
        dry_run = dialog.addButton("Dry Run", QMessageBox.ButtonRole.ActionRole)
        real = dialog.addButton("Real Measurement", QMessageBox.ButtonRole.ActionRole)
        dialog.addButton(QMessageBox.StandardButton.Cancel)
        dialog.exec()
        selected = dialog.clickedButton()
        if selected is simulation:
            return "Simulation"
        if selected is dry_run:
            return "Dry Run"
        if selected is real:
            if self.motion_authorization != "OPERATIONAL":
                QMessageBox.warning(self, "Hardware Scan Locked", "Select OPERATIONAL authorization before Real Measurement.")
                return None
            blockers = self.real_measurement_blockers()
            if blockers:
                QMessageBox.warning(
                    self,
                    "Real Measurement Not Ready",
                    "Real Measurement remains locked:\n\n"
                    + "\n".join(f"- {blocker}" for blocker in blockers),
                )
                return None
            return "Real Scan"
        return None

    def real_measurement_blockers(self) -> tuple[str, ...]:
        """Read-only dual-USB and Mega commissioning gate for hardware scans."""

        damage_lockout_path = PROJECT_ROOT / "config" / "crtouch_hardware_lockout.json"
        if damage_lockout_path.is_file():
            try:
                damage_lockout = json.loads(
                    damage_lockout_path.read_text(encoding="utf-8")
                )
            except Exception as exc:
                return (f"CR Touch safety lockout file is unreadable: {exc}",)
            if damage_lockout.get("active"):
                return (
                    "CR Touch mechanical-crash lockout is active. Disconnect power, "
                    "inspect the probe/mount/carriage, and explicitly clear the "
                    "inspection record before any real motion.",
                )

        profile_blockers = mount_profile_blockers(PROJECT_ROOT)
        if profile_blockers:
            return profile_blockers

        port_map = discover_spm_ports()
        mega_info = None
        mega_status = None
        handshake_error = ""
        if len(port_map.mega) == 1:
            try:
                with MegaProbeSerialTransport(port_map.mega[0].device) as mega:
                    mega_info = mega.get_info()
                    mega_status = mega.get_status()
            except Exception as exc:
                handshake_error = str(exc)
        report = evaluate_spm_readiness(port_map, mega_info)
        blockers = list(report.blockers)
        if mega_status is not None:
            if mega_status.trigger_raw:
                blockers.append(
                    "CR Touch trigger is active/latched. Probe In, RESET and "
                    "CLEAR_TRIGGER must restore the D3 baseline before motion."
                )
            if mega_status.fault_code:
                blockers.append(
                    f"Mega CR Touch fault is active: {mega_status.fault_code}"
                )
        if handshake_error:
            blockers.append(f"Mega probe handshake failed: {handshake_error}")
        if len(port_map.mk4s) == 1:
            mk4s_evidence = connect_real_hardware_readonly(
                port=port_map.mk4s[0].device
            )
            if not mk4s_evidence.get("ok"):
                blockers.append(
                    "MK4S Stage 2 read-only thermal check failed: "
                    + str(mk4s_evidence.get("message", "unknown error"))
                )
            else:
                blockers.extend(
                    stage2_thermal_blockers(
                        str(mk4s_evidence.get("temperature", ""))
                    )
                )
        self.append_log(
            "[REAL MEASUREMENT GATE] "
            + ("ready" if not blockers else "; ".join(blockers))
        )
        return tuple(blockers)

    def test_mega_probe_connection(self) -> None:
        """Run a read-only identity, state and self-test check on the Mega."""

        candidates = discover_mega_candidate_ports()
        status_label = self.crtouch_prep_window.mega_status
        if not candidates:
            message = (
                "No Arduino Mega candidate was found. Connect its USB cable, "
                "flash the locked SPM firmware, then retry."
            )
            status_label.setText(f"Mega 2560: not found · {message}")
            status_label.setStyleSheet(
                "padding:8px; background:#fff0f0; border:1px solid #b42318;"
            )
            self.append_log(f"[MEGA PROBE TEST] {message}")
            return

        failures: list[str] = []
        for port in candidates:
            try:
                with MegaProbeSerialTransport(port) as mega:
                    info = mega.get_info()
                    status = mega.get_status()
                    self_test_ok = mega.self_test()
                safe = (
                    status.actuation_locked
                    and not status.trigger_raw
                    and status.fault_code is None
                )
                is_contact = bool(status.trigger_raw or (status.state == "CONTACT_LATCHED"))
                result = (
                    f"Mega 2560 on {port}: identity verified · firmware "
                    f"{info.firmware_version} · trigger={int(status.trigger_raw)} · "
                    f"actuation locked={int(status.actuation_locked)} · "
                    f"self-test={'PASS' if self_test_ok else 'FAIL'}"
                )
                status_label.setText(result)
                status_label.setStyleSheet(
                    "padding:8px; background:#e7f7ed; border:1px solid #238636;"
                    if safe and self_test_ok
                    else "padding:8px; background:#fff0f0; border:1px solid #b42318;"
                )
                if hasattr(self, "deflection"):
                    self.deflection.setText(
                        f"Deflection: {'CONTACT' if is_contact else 'OPEN'} [Arduino D3={int(status.trigger_raw)}]"
                    )
                    self.deflection.setStyleSheet(
                        "border: 2px solid #dc2626; padding: 8px; background: #fee2e2; color: #7f1d1d; font-weight: 800;"
                        if is_contact else
                        "border: 2px solid #16a34a; padding: 8px; background: #dcfce7; color: #14532d; font-weight: 800;"
                    )
                if hasattr(self, "z_state"):
                    self.z_state.setText(f"Arduino CR-Touch: {status.state} (D3={int(status.trigger_raw)})")
                self.append_log(f"[MEGA PROBE TEST] {result}")
                return
            except Exception as exc:
                failures.append(f"{port}: {exc}")

        message = "No candidate returned the SPM Mega identity. " + "; ".join(failures)
        status_label.setText(f"Mega 2560: handshake failed · {message}")
        status_label.setStyleSheet(
            "padding:8px; background:#fff0f0; border:1px solid #b42318;"
        )
        self.append_log(f"[MEGA PROBE TEST] {message}")

    def build_menu_bar(self) -> None:
        menu = self.menuBar()

        file_menu = menu.addMenu("File")
        download_log = QAction("Download Live Log", self)
        download_log.triggered.connect(self.download_log)
        clear_log = QAction("Clear Live Log", self)
        clear_log.triggered.connect(self.clear_log)
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.request_safe_exit)
        file_menu.addAction(download_log)
        file_menu.addAction(clear_log)
        file_menu.addSeparator()
        file_menu.addAction(exit_action)

        view_menu = menu.addMenu("View")
        clear_trace = QAction("Clear Z Trace", self)
        clear_trace.triggered.connect(lambda: self.z_trace.clear() if hasattr(self, "z_trace") else None)
        view_menu.addAction(clear_trace)
        view_menu.addSeparator()
        for mode_key, menu_label in (("line", "Line Mode"), ("topography", "Topography")):
            direction_menu = view_menu.addMenu(menu_label)
            for direction in ("X+", "X-", "Y+", "Y-"):
                direction_menu.addAction(
                    direction,
                    lambda _checked=False, selected_mode=mode_key, selected_direction=direction:
                        self.open_signal_window(selected_mode, selected_direction),
                )
        view_menu.addAction("Open All Direction Windows", self.open_all_signal_windows)

        tools_menu = menu.addMenu("Tools")
        tools_menu.addAction("Scan Control", self.open_z_scanner_window)
        simulation_menu = tools_menu.addMenu("Simulation Mode")
        self.simulation_menu_action = QAction("Enable Simulation", self, checkable=True)
        self.simulation_menu_action.setChecked(self.simulation_engine.is_active)
        self.simulation_menu_action.toggled.connect(self.set_simulation_enabled)
        simulation_menu.addAction(self.simulation_menu_action)
        sample_menu = simulation_menu.addMenu("Sample Selection")
        for sample_type in SampleGenerator.SAMPLE_TYPES:
            label = self.simulation_sample_label(sample_type)
            sample_menu.addAction(label, lambda _checked=False, value=label: self.select_simulation_sample(value))
        simulation_menu.addSeparator()
        simulation_menu.addAction("Sample Parameters…", self.open_simulation_configuration)
        simulation_menu.addAction("Show Topography Preview", self.open_simulation_configuration)
        tools_menu.addSeparator()
        tools_menu.addAction("Live Log", self.open_live_log_window)
        tools_menu.addAction("Local AI Print File Export", self.open_academic_gcode_window)
        tools_menu.addAction("CR Touch Probe Prep", self.open_crtouch_prep_window)
        tools_menu.addAction(
            "Discover and Refine Raised Objects…",
            self.start_two_object_adaptive_scan,
        )
        tools_menu.addSeparator()
        tools_menu.addAction("Connect Read-Only", self.connect_system)
        tools_menu.addAction("Run Diagnosis", self.run_diagnosis)
        tools_menu.addAction("Safe Standby", self.safe_standby)
        tools_menu.addAction("AI Error Correction", self.ai_error_correction)

        about_menu = menu.addMenu("About")
        about_menu.addAction("About SPM Operator Software", self.show_about)

    def start_two_object_adaptive_scan(self) -> bool:
        """Run the verified overview-to-focused real-hardware protocol."""

        if self.worker and self.worker.isRunning():
            QMessageBox.warning(
                self,
                "Measurement Busy",
                "Another hardware or measurement command is already running.",
            )
            return False
        if not self.system_connected:
            QMessageBox.warning(
                self,
                "Connect MK4S First",
                "Connect the MK4S through the main software before starting the real scan.",
            )
            return False
        if self.motion_authorization != "OPERATIONAL":
            QMessageBox.warning(
                self,
                "Real Measurement Locked",
                "Select OPERATIONAL authorization before running adaptive discovery.",
            )
            return False
        blockers = self.real_measurement_blockers()
        if blockers:
            QMessageBox.warning(
                self,
                "Adaptive Object Scan Not Ready",
                "The real-hardware readiness gate remains locked:\n\n"
                + "\n".join(f"- {blocker}" for blocker in blockers),
            )
            return False

        confirmation = QMessageBox(self)
        confirmation.setWindowTitle("Authorize Adaptive Raised-Object Scan")
        confirmation.setIcon(QMessageBox.Icon.Warning)
        resolution = str(self.two_object_resolution.currentData() or "high")
        resolution_profile = TWO_MAGNET_RESOLUTION_PROFILES[resolution]
        mount = load_mount_profiles(PROJECT_ROOT)["profile"]
        envelope = mount["native_scan_envelope_mm"]
        bare_z = float(mount["local_bare_stage_trigger_z_mm"])
        safe_z = float(mount["safe_travel_z_mm"])
        raised_floor = bare_z + 9.5
        confirmation.setText("Survey the full field and refine discovered objects?")
        confirmation.setInformativeText(
            "REAL HARDWARE WILL MOVE\n\n"
            f"Centered Stage 2 field: X {envelope['x_min']:.2f}–"
            f"{envelope['x_max']:.2f} mm, Y {envelope['y_min']:.2f}–"
            f"{envelope['y_max']:.2f} mm\n"
            f"Resolution profile: {resolution.upper()}\n"
            f"Discovery pitch: {resolution_profile['coarse_pitch_mm']:.1f} mm\n"
            f"Focused map pitch: {resolution_profile['focused_pitch_mm']:.1f} mm\n"
            f"Bare-stage trigger reference: Z{bare_z:.2f} mm\n"
            f"Raised-object search floor: Z{raised_floor:.2f} mm\n"
            f"Safe XY travel and final retract: Z{safe_z:.2f} mm\n\n"
            "This profile is calibrated for raised objects approximately "
            "9.5–12.0 mm above the stage.\n\n"
            "Confirm all objects are fixed, the path is clear, the CR Touch is "
            "cool and stowed, and hands are outside the machine."
        )
        start_button = confirmation.addButton(
            "Authorize and Start Real Scan",
            QMessageBox.ButtonRole.AcceptRole,
        )
        confirmation.addButton(QMessageBox.StandardButton.Cancel)
        confirmation.exec()
        if confirmation.clickedButton() is not start_button:
            self.append_log("[TWO-OBJECT SCAN] Operator cancelled before motion.")
            return False

        worker = TwoObjectAdaptiveScanWorker(resolution)
        worker.log_line.connect(self.handle_two_object_scan_line)
        worker.finished_payload.connect(self.finish_two_object_adaptive_scan)
        worker.finished.connect(lambda: setattr(self, "worker", None))
        self.worker = worker
        self.latest_two_object_result = {}
        self.repeat_two_object_button.setEnabled(False)
        if self.z_scanner_window is not None:
            self.z_scanner_window.scan_progress.setValue(0)
            self.z_scanner_window.scan_progress.setFormat("Object discovery · %p%")
            self.z_scanner_window.update_instrument_state(
                connected=True,
                motion_enabled=True,
                acquisition="Adaptive Object Discovery",
            )
            self.z_scanner_window.show()
            self.z_scanner_window.raise_()
        self.append_log(
            "[ADAPTIVE OBJECT SCAN] Authorized real-hardware run started: "
            f"verified envelope, {resolution} resolution, "
            f"{resolution_profile['focused_pitch_mm']:.1f} mm focused pitch."
        )
        worker.start()
        return True

    def handle_two_object_scan_line(self, line: str) -> None:
        """Show persistent runner evidence and update the visible progress bar."""

        self.append_log(f"[ADAPTIVE OBJECT] {line}")
        match = __import__("re").search(r"COARSE\s+(\d+)/(\d+)", line)
        if match and self.z_scanner_window is not None:
            sequence, total = map(int, match.groups())
            progress = min(55, max(1, round(sequence * 55 / total)))
            self.z_scanner_window.scan_progress.setValue(progress)
            self.z_scanner_window.point_readout.setText(
                f"Coarse discovery {sequence}/{total} · adaptive feedback active"
            )
        map_match = __import__("re").search(
            r"MAP (?:object|magnet)=(\d+)\s+(\d+)/(\d+)", line
        )
        if map_match and self.z_scanner_window is not None:
            magnet, sequence, total = map(int, map_match.groups())
            base = 55 if magnet == 1 else 77
            progress = min(99, base + round(sequence * 22 / total))
            self.z_scanner_window.scan_progress.setValue(progress)
            self.z_scanner_window.point_readout.setText(
                f"Focused map · object {magnet} · {sequence}/{total}"
            )
        if (
            "COARSE_OBJECTS" in line or "COARSE_CENTERS" in line
        ) and self.z_scanner_window is not None:
            self.z_scanner_window.session_message.setText(
                "Separated contact regions found. Refining each 2D boundary."
            )

    def finish_two_object_adaptive_scan(self, payload: dict[str, Any]) -> None:
        """Present retained evidence and keep the hardware state explicit."""

        self.latest_two_object_result = dict(payload)
        self.repeat_two_object_button.setEnabled(True)
        summary = payload.get("summary") or {}
        ok = bool(payload.get("ok"))
        if self.z_scanner_window is not None:
            self.z_scanner_window.scan_progress.setValue(100 if ok else 0)
            self.z_scanner_window.scan_progress.setFormat(
                "Adaptive object scan PASS" if ok else "Adaptive object scan FAILED"
            )
            self.z_scanner_window.update_instrument_state(
                connected=self.system_connected,
                motion_enabled=False,
                acquisition="Complete" if ok else "Fault / verify Z",
            )
        if not ok:
            QMessageBox.critical(
                self,
                "Adaptive Object Scan Failed",
                f"{payload.get('message', 'Unknown scan failure')}\n\n"
                "Verify that the CR Touch is stowed and the MK4S is at Z120 "
                "before attempting another command.",
            )
            return

        centers = summary.get("detected_centers_map_mm") or []
        plot_path = Path(str(summary.get("plot", "")))
        self.append_log(
            "[TWO-OBJECT SCAN PASS] "
            f"measurements={summary.get('readings')} "
            f"contacts={summary.get('contacts')} centers={centers} "
            f"safe_Z={summary.get('safe_z_mm', 45.0)}"
        )
        result = QMessageBox(self)
        result.setWindowTitle("Adaptive Object Scan Complete")
        result.setIcon(QMessageBox.Icon.Information)
        result.setText(
            f"Adaptive scan passed and the probe is In at safe "
            f"Z{summary.get('safe_z_mm', 45.0):.2f}."
        )
        result.setInformativeText(
            f"Resolution: {summary.get('resolution_profile')}\n"
            f"Physical measurements: {summary.get('readings')}\n"
            f"Physical contacts: {summary.get('contacts')}\n"
            f"Detected objects: {summary.get('detected_object_count', len(centers))}\n"
            f"Detected map centers: {centers}\n\n"
            f"CSV: {summary.get('csv')}\n"
            f"Plot: {summary.get('plot')}\n"
            f"Summary: {payload.get('summary_path')}"
        )
        open_plot = result.addButton("Open Result Plot", QMessageBox.ButtonRole.ActionRole)
        open_handbook = result.addButton("Open Handbook", QMessageBox.ButtonRole.ActionRole)
        result.addButton(QMessageBox.StandardButton.Close)
        result.exec()
        if result.clickedButton() is open_plot and plot_path.is_file():
            os.startfile(str(plot_path))
        elif result.clickedButton() is open_handbook:
            self.open_project_handbook()

    def request_safe_exit(self) -> None:
        self.append_system_message("Close requested. Applying the safe shutdown policy.")
        self.close()

    def closeEvent(self, event: Any) -> None:  # noqa: N802
        if self._safe_close_approved:
            event.accept()
            return
        event.ignore()
        if self._safe_close_in_progress:
            return
        self.begin_safe_shutdown()

    def begin_safe_shutdown(self) -> None:
        """Run stop, park, and disconnect asynchronously so the UI remains responsive."""
        self._safe_close_in_progress = True
        self._safe_close_wait_attempts = 0
        self.stop_measurement()
        if self.worker and self.worker.isRunning():
            request_real_scan_stop()
            z_stop_now()
            self.append_system_message("Safe close: stop requested; waiting for active command.")
            QTimer.singleShot(250, self._continue_safe_shutdown_when_idle)
            return
        self._start_safe_shutdown_worker()

    def _continue_safe_shutdown_when_idle(self) -> None:
        if self.worker and self.worker.isRunning():
            self._safe_close_wait_attempts += 1
            if self._safe_close_wait_attempts >= 120:
                self._safe_close_in_progress = False
                QMessageBox.warning(
                    self,
                    "Safe Shutdown Waiting",
                    "The active command did not stop within 30 seconds. The software remains open. "
                    "Use HALT / STOP Z, verify the hardware, then close again.",
                )
                return
            QTimer.singleShot(250, self._continue_safe_shutdown_when_idle)
            return
        self._start_safe_shutdown_worker()

    def _start_safe_shutdown_worker(self) -> None:
        self._safe_close_progress = QProgressDialog(
            "Safe shutdown in progress...\n\n1. Park X125 Y105 Z120\n2. Verify safe position\n3. Disconnect\n4. Close",
            "",
            0,
            0,
            self,
        )
        self._safe_close_progress.setWindowTitle("Safe Shutdown")
        self._safe_close_progress.setCancelButton(None)
        self._safe_close_progress.setWindowModality(Qt.WindowModality.ApplicationModal)
        self._safe_close_progress.setMinimumDuration(0)
        self._safe_close_progress.show()
        connected = bool(self.system_connected)
        motion_authorized = os.getenv("SPM_WEB_ALLOW_HEALTH_MOTION", "0").strip() == "1"

        def shutdown_action() -> dict[str, Any]:
            stages: list[dict[str, Any]] = []
            if connected and motion_authorized:
                standby = system_safe_standby_for_close()
                stages.append(standby)
                if not standby.get("ok"):
                    return {"ok": False, "status": "park_failed", "message": standby.get("message", "Safe park failed."), "stages": stages}
            disconnect = system_disconnect()
            stages.append(disconnect)
            return {
                "ok": bool(disconnect.get("ok")),
                "status": "safe_close_complete" if disconnect.get("ok") else "disconnect_failed",
                "message": disconnect.get("message", "Disconnect failed."),
                "stages": stages,
            }

        worker = Worker(shutdown_action)
        worker.finished_payload.connect(self._finish_safe_shutdown)
        worker.finished.connect(lambda: setattr(self, "worker", None))
        self.worker = worker
        worker.start()

    def _finish_safe_shutdown(self, payload: dict[str, Any]) -> None:
        if self._safe_close_progress is not None:
            self._safe_close_progress.close()
            self._safe_close_progress = None
        for stage in payload.get("stages", []):
            self.render_payload_log(stage)
        if not payload.get("ok"):
            self._safe_close_in_progress = False
            QMessageBox.warning(self, "Safe Shutdown Blocked", str(payload.get("message", "Safe shutdown failed.")))
            return
        self.system_connected = False
        self._safe_close_in_progress = False
        self._safe_close_approved = True
        self.append_log("[SAFE CLOSE] Shutdown completed; see stage results for parking and disconnection.")
        self.close()

    def build_system_panel(self) -> QWidget:
        """Left control panel — Device Connection & Preparation.

        Four labeled zones (NanoScope / SmartScan style):
        1. CONNECTION  — port select, connect/disconnect
        2. AUTHORIZATION — LOCKED/STANDBY/OPERATIONAL (always visible, no tab needed)
        3. SAFETY      — E-Stop (large red)
        4. SERVICE     — diagnostics, standby, close
        """
        scroll_area_widget = QWidget()
        outer_layout = QVBoxLayout(scroll_area_widget)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        def _section_label(text: str) -> QLabel:
            lbl = QLabel(text)
            lbl.setStyleSheet(
                "font-size: 10px; font-weight: 700; color: #6B7280; letter-spacing: 1px;"
                "padding: 10px 12px 4px 12px; background: transparent;"
            )
            return lbl

        def _separator() -> QFrame:
            sep = QFrame()
            sep.setFrameShape(QFrame.Shape.HLine)
            sep.setStyleSheet("color: #E5E7EB;")
            sep.setFixedHeight(1)
            return sep

        # ── 1. CONNECTION ─────────────────────────────────────────────────────
        outer_layout.addWidget(_section_label("CONNECTION"))
        conn_widget = QWidget()
        conn_widget.setStyleSheet("background: #FFFFFF; border-bottom: 1px solid #E5E7EB;")
        conn_layout = QVBoxLayout(conn_widget)
        conn_layout.setContentsMargins(12, 8, 12, 12)
        conn_layout.setSpacing(6)

        self.connection_badge = QLabel("● OFFLINE")
        self.connection_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.connection_badge.setStyleSheet(
            "font-weight: 800; color: #7F1D1D; background: #FEE2E2;"
            "border: 1px solid #DC2626; padding: 8px; border-radius: 4px;"
        )
        conn_layout.addWidget(self.connection_badge)

        connection_help = QLabel("Read-only handshake: firmware · temperature · endstops · position. No motion.")
        connection_help.setWordWrap(True)
        connection_help.setStyleSheet("color: #6B7280; font-size: 10px; padding: 2px 0;")
        conn_layout.addWidget(connection_help)

        port_row = QHBoxLayout()
        port_label = QLabel("Port")
        port_label.setStyleSheet("font-weight: 600; color: #374151;")
        self.port_select = QComboBox()
        self.port_select.setEditable(True)
        self.port_select.addItem("AUTO")
        self.refresh_ports(announce=False)
        port_row.addWidget(port_label)
        port_row.addWidget(self.port_select, 1)
        conn_layout.addLayout(port_row)

        refresh = QPushButton("↺  Refresh Ports")
        refresh.setToolTip("Rescan available serial ports.")
        refresh.clicked.connect(self.refresh_ports)
        self.refresh_button = refresh
        conn_layout.addWidget(refresh)

        self.connect_button = QPushButton("Connect Hardware")
        self.connect_button.setStyleSheet(YELLOW_BUTTON_STYLE)
        self.connect_button.setMinimumHeight(40)
        self.connect_button.clicked.connect(self.connect_system)

        self.disconnect_button = QPushButton("Disconnect")
        self.disconnect_button.setStyleSheet(RED_BUTTON_STYLE)
        self.disconnect_button.setEnabled(False)
        self.disconnect_button.clicked.connect(self.disconnect_system)

        conn_btns = QHBoxLayout()
        conn_btns.addWidget(self.connect_button, 2)
        conn_btns.addWidget(self.disconnect_button, 1)
        conn_layout.addLayout(conn_btns)

        self.system_state = QLabel("System: not connected")
        self.system_state.setWordWrap(True)
        self.system_state.setMinimumHeight(170)
        self.system_state.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.system_state.setStyleSheet(
            "color: #374151; border: 1px solid #E5E7EB; padding: 8px; background: #FAFBFC;"
            "border-radius: 4px; font-size: 11px;"
        )
        conn_layout.addWidget(self.system_state, 1)
        conn_layout.addWidget(QLabel("Connection activity"))
        self.system_log = QTextEdit()
        self.system_log.setReadOnly(True)
        self.system_log.setMaximumHeight(90)
        self.system_log.setStyleSheet(
            "font-family: 'Consolas', 'Ubuntu Mono', monospace; font-size: 10px;"
            "background: #FAFBFC; border: 1px solid #E5E7EB; border-radius: 4px;"
        )
        self.system_log.setPlainText("Hardware interface ready. Select AUTO or /dev/spm-mk4s, then connect.")
        conn_layout.addWidget(self.system_log)

        outer_layout.addWidget(conn_widget)

        # ── 2. MOTION AUTHORIZATION (always visible) ─────────────────────────
        outer_layout.addWidget(_section_label("MOTION AUTHORIZATION"))
        auth_widget = QWidget()
        auth_widget.setStyleSheet("background: #FFFFFF; border-bottom: 1px solid #E5E7EB;")
        auth_layout = QVBoxLayout(auth_widget)
        auth_layout.setContentsMargins(12, 8, 12, 12)
        auth_layout.setSpacing(4)

        auth_note = QLabel("Select authorization level. OPERATIONAL requires connected hardware.")
        auth_note.setWordWrap(True)
        auth_note.setStyleSheet("color: #6B7280; font-size: 10px; padding: 0 0 4px 0;")
        auth_layout.addWidget(auth_note)

        # Hidden combo kept for backward compatibility (other methods use it)
        self.authorization_select = QComboBox()
        self.authorization_select.addItems(["LOCKED", "STANDBY", "OPERATIONAL"])
        self.authorization_select.setVisible(False)
        self.authorization_select.currentTextChanged.connect(self.apply_motion_authorization)
        auth_layout.addWidget(self.authorization_select)

        # Professional radio button group (visible to operator)
        self._auth_radio_group = QButtonGroup(self)
        self._auth_radios: dict[str, QRadioButton] = {}
        for auth_level, description, color in [
            ("LOCKED",      "No motion — safe default",         "#6B7280"),
            ("STANDBY",     "Z approach & retract authorized",  "#1D4ED8"),
            ("OPERATIONAL", "Full XY + Z scan authorized",      "#16A34A"),
        ]:
            radio = QRadioButton(f"  {auth_level}")
            radio.setToolTip(description)
            radio.setStyleSheet(f"font-weight: 700; color: {color};")
            self._auth_radio_group.addButton(radio)
            self._auth_radios[auth_level] = radio
            desc_label = QLabel(f"    {description}")
            desc_label.setStyleSheet("font-size: 10px; color: #6B7280; padding: 0 0 4px 24px;")
            auth_layout.addWidget(radio)
            auth_layout.addWidget(desc_label)
            radio.toggled.connect(
                lambda checked, lvl=auth_level: (
                    self.authorization_select.setCurrentText(lvl) if checked else None
                )
            )
        self._auth_radios["LOCKED"].setChecked(True)

        outer_layout.addWidget(auth_widget)

        # ── 3. SAFETY ─────────────────────────────────────────────────────────
        outer_layout.addWidget(_section_label("SAFETY"))
        safety_widget = QWidget()
        safety_widget.setStyleSheet("background: #FFFFFF; border-bottom: 1px solid #E5E7EB;")
        safety_layout = QVBoxLayout(safety_widget)
        safety_layout.setContentsMargins(12, 8, 12, 12)
        safety_layout.setSpacing(6)

        emergency = QPushButton("🛑  EMERGENCY STOP")
        emergency.setToolTip("IMMEDIATE STOP. Latches E-STOP gate — requires manual reset.")
        emergency.setStyleSheet(RED_BUTTON_STYLE)
        emergency.setMinimumHeight(50)
        emergency.setFont(emergency.font())
        emergency.clicked.connect(self.stop_z)
        safety_layout.addWidget(emergency)

        outer_layout.addWidget(safety_widget)

        # ── 4. SERVICE ────────────────────────────────────────────────────────
        outer_layout.addWidget(_section_label("SERVICE"))
        service_widget = QWidget()
        service_widget.setStyleSheet("background: #FFFFFF;")
        service_layout = QVBoxLayout(service_widget)
        service_layout.setContentsMargins(12, 8, 12, 12)
        service_layout.setSpacing(6)

        diagnosis = QPushButton("Diagnosis")
        calibration = QPushButton("Calibrate MK4S")
        ai_fix = QPushButton("AI Error Correction")
        standby = QPushButton("Safe Standby X125 Y105 Z120")
        close_button = QPushButton("Close Safely")

        for button in (diagnosis, calibration, ai_fix, standby, close_button):
            button.setMinimumHeight(38)

        diagnosis.setStyleSheet(GRAY_BUTTON_STYLE)
        calibration.setStyleSheet(GRAY_BUTTON_STYLE)
        ai_fix.setStyleSheet(GRAY_BUTTON_STYLE)
        standby.setStyleSheet(GRAY_BUTTON_STYLE)
        close_button.setStyleSheet(GRAY_BUTTON_STYLE)

        diagnosis.clicked.connect(self.run_diagnosis)
        calibration.clicked.connect(self.run_calibration)
        ai_fix.clicked.connect(self.ai_error_correction)
        standby.clicked.connect(self.safe_standby)
        close_button.clicked.connect(self.request_safe_exit)

        self.diagnosis_button = diagnosis
        self.calibration_button = calibration
        self.standby_button = standby
        self.ai_fix_button = ai_fix

        self.readonly_buttons = (diagnosis,)
        self.motion_buttons = (calibration, standby)
        self.advanced_buttons = self.motion_buttons

        diagnosis.setEnabled(False)
        calibration.setEnabled(False)
        standby.setEnabled(False)

        svc_grid = QGridLayout()
        svc_grid.addWidget(diagnosis, 0, 0)
        svc_grid.addWidget(calibration, 0, 1)
        svc_grid.addWidget(ai_fix, 1, 0, 1, 2)
        service_layout.addLayout(svc_grid)

        shutdown_row = QHBoxLayout()
        shutdown_row.addWidget(standby, 2)
        shutdown_row.addWidget(close_button, 1)
        service_layout.addLayout(shutdown_row)

        outer_layout.addWidget(service_widget)
        outer_layout.addStretch(1)

        scroll_area_widget.setMinimumWidth(380)
        return scroll_area_widget

    def build_z_panel(self) -> QGroupBox:
        box = QGroupBox("Z Scanner")
        layout = QVBoxLayout()

        readouts = QHBoxLayout()
        self.current_z = QLabel("Current Z: --")
        self.count_z = QLabel("Count Z: --")
        self.clearance = QLabel("Clearance: --")
        self.deflection = QLabel("Deflection: --")
        for label in (self.current_z, self.count_z, self.clearance, self.deflection):
            label.setStyleSheet("border: 1px solid #8da2b8; padding: 8px; background: #f8fbff;")
            readouts.addWidget(label)
        layout.addLayout(readouts)

        self.z_trace = ZTraceWidget()
        layout.addWidget(self.z_trace, 1)

        scale_row = QHBoxLayout()
        full = QPushButton("Full")
        auto = QPushButton("Auto")
        zoom = QPushButton("Zoom")
        self.zoom_mm = QDoubleSpinBox()
        self.zoom_mm.setRange(0.01, 50.0)
        self.zoom_mm.setDecimals(3)
        self.zoom_mm.setSingleStep(0.1)
        self.zoom_mm.setValue(2.0)
        full.clicked.connect(lambda: self.z_trace.set_view_mode("full"))
        auto.clicked.connect(lambda: self.z_trace.set_view_mode("auto"))
        zoom.clicked.connect(lambda: self.z_trace.set_view_mode("zoom"))
        self.zoom_mm.valueChanged.connect(self.z_trace.set_zoom_window)
        scale_row.addWidget(QLabel("Chart Viewport"))
        scale_row.addWidget(full)
        scale_row.addWidget(auto)
        scale_row.addWidget(zoom)
        scale_row.addWidget(QLabel("Window Width (mm)"))
        scale_row.addWidget(self.zoom_mm)
        layout.addLayout(scale_row)

        form = QFormLayout()
        self.target_z = QDoubleSpinBox()
        self.target_z.setRange(0.0, 221.0)
        self.target_z.setDecimals(3)
        self.target_z.setSingleStep(0.1)
        self.target_z.setValue(0.0)
        self.target_z.lineEdit().returnPressed.connect(self.apply_target_z)
        self.clearance_setpoint = QDoubleSpinBox()
        self.clearance_setpoint.setRange(0.0, 20.0)
        self.clearance_setpoint.setDecimals(3)
        self.clearance_setpoint.setSingleStep(0.1)
        self.clearance_setpoint.setValue(1.0)
        self.feedback_gain = QDoubleSpinBox()
        self.feedback_gain.setRange(0.01, 20.0)
        self.feedback_gain.setDecimals(3)
        self.feedback_gain.setValue(1.0)
        self.tapping_range = QDoubleSpinBox()
        self.tapping_range.setRange(0.1, 221.0)
        self.tapping_range.setDecimals(3)
        self.tapping_range.setSingleStep(0.1)
        self.tapping_range.setValue(20.0)
        self.contact_limit = QDoubleSpinBox()
        self.contact_limit.setRange(0.0, 221.0)
        self.contact_limit.setDecimals(3)
        self.contact_limit.setSingleStep(0.001)
        self.contact_limit.setValue(54.0)
        self.contact_limit.setStyleSheet("background:#fff0c2; font-weight:700;")
        self.contact_limit.setToolTip("Safety clamp; never command below this Z without validated contact detection.")
        self.expected_surface_z = QDoubleSpinBox()
        self.expected_surface_z.setRange(0.0, 221.0)
        self.expected_surface_z.setDecimals(3)
        self.expected_surface_z.setSingleStep(0.1)
        self.expected_surface_z.setValue(8.0)
        self.approach_speed = QDoubleSpinBox()
        self.approach_speed.setRange(0.01, 40.0)
        self.approach_speed.setDecimals(3)
        self.approach_speed.setSingleStep(0.05)
        self.approach_speed.setValue(2.0)
        self.fine_approach_speed = QDoubleSpinBox()
        self.fine_approach_speed.setRange(0.01, 2.0)
        self.fine_approach_speed.setDecimals(3)
        self.fine_approach_speed.setValue(0.1)
        self.fine_approach_speed.setToolTip("Fine speed for the final touchdown region.")
        self.tap_retract_z = QDoubleSpinBox()
        self.tap_retract_z.setRange(0.1, 30.0)
        self.tap_retract_z.setDecimals(3)
        self.tap_retract_z.setValue(3.0)
        self.full_retract_z = QDoubleSpinBox()
        self.full_retract_z.setRange(0.1, 221.0)
        self.full_retract_z.setDecimals(3)
        self.full_retract_z.setValue(120.0)
        form.addRow("Setpoint (Target) mm", self.target_z)
        form.addRow("Contact Limit (Safety Clamp) mm", self.contact_limit)
        form.addRow("Tapping range above setpoint mm", self.tapping_range)
        form.addRow("Expected surface Z mm", self.expected_surface_z)
        form.addRow("Coarse Approach Speed mm/s", self.approach_speed)
        form.addRow("Fine Approach Speed mm/s", self.fine_approach_speed)
        wz_row = QHBoxLayout()
        wz_row.addWidget(QLabel("0.000 mm - scanner plate / XY table"))
        set_wz = QPushButton("Set to Current")
        set_wz.setToolTip("Set workpiece zero from the latest measured Z reference; no motion is commanded.")
        wz_row.addWidget(set_wz)
        form.addRow("Workpiece Zero (WZ)", wz_row)
        form.addRow("Safe Park Height mm", self.full_retract_z)
        layout.addLayout(form)

        actions = QHBoxLayout()
        read = QPushButton("Measure Reference")
        check_probe = QPushButton("Read Probe (Arduino)")
        advisor = QPushButton("Engage Intelligence")
        apply = QPushButton("Jog to Surface")
        auto_approach = QPushButton("Auto-Engage")
        retract = QPushButton("Emergency Retract")
        stop = QPushButton("HALT")
        stop.setToolTip("STOP Z immediately")
        check_probe.setStyleSheet(GREEN_BUTTON_STYLE)
        check_probe.setToolTip("Read real-time CR-Touch probe feedback from Arduino Mega without motion.")
        advisor.setStyleSheet(GRAY_BUTTON_STYLE)
        for button in (apply, auto_approach):
            button.setStyleSheet(GREEN_BUTTON_STYLE)
        for button in (retract, stop):
            button.setStyleSheet(RED_BUTTON_STYLE)
        read.clicked.connect(self.read_z)
        check_probe.clicked.connect(self.test_mega_probe_connection)
        advisor.clicked.connect(self.run_approach_advisor)
        apply.clicked.connect(self.apply_target_z)
        auto_approach.clicked.connect(self.auto_approach_z)
        retract.clicked.connect(self.retract_z)
        stop.clicked.connect(self.stop_z)
        self.z_motion_buttons = (apply, auto_approach, retract)
        actions.addWidget(read)
        actions.addWidget(check_probe)
        actions.addWidget(advisor)
        actions.addWidget(apply)
        actions.addWidget(auto_approach)
        actions.addWidget(retract)
        actions.addWidget(stop)
        layout.addLayout(actions)

        self.z_state = QLabel("Z scanner: ready")
        self.z_state.setWordWrap(True)
        self.z_state.setStyleSheet("border: 1px solid #8da2b8; padding: 8px; background: #f8fbff;")
        layout.addWidget(self.z_state)
        box.setLayout(layout)
        return box

    def build_log_panel(self) -> QGroupBox:
        box = QGroupBox("Live Log")
        layout = QVBoxLayout()
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setStyleSheet("font-family: Consolas, monospace;")
        buttons = QHBoxLayout()
        clear = QPushButton("Clear Log")
        download = QPushButton("Download Log")
        clear.clicked.connect(self.clear_log)
        download.clicked.connect(self.download_log)
        buttons.addStretch(1)
        buttons.addWidget(clear)
        buttons.addWidget(download)
        layout.addLayout(buttons)
        layout.addWidget(self.log)
        box.setLayout(layout)
        return box

    def selected_port(self) -> str:
        port = self.port_select.currentText()
        return "" if port == "AUTO" else port

    def refresh_ports(self, _checked: bool = False, *, announce: bool = True) -> None:
        previous = self.port_select.currentText().strip() if self.port_select.count() else "AUTO"
        ports = discover_ports()
        self.port_select.blockSignals(True)
        self.port_select.clear()
        self.port_select.addItem("AUTO")
        for port in ports:
            label = port.device
            self.port_select.addItem(label, port)
            self.port_select.setItemData(
                self.port_select.count() - 1,
                f"{port.description}\n{port.hardware_id}".strip(),
                Qt.ItemDataRole.ToolTipRole,
            )
        if previous and (previous == "AUTO" or self.port_select.findText(previous) >= 0):
            self.port_select.setCurrentText(previous)
        elif ports:
            self.port_select.setCurrentText(ports[0].device)
        else:
            self.port_select.setCurrentText(previous or "AUTO")
        self.port_select.blockSignals(False)
        if announce:
            devices = ", ".join(port.device for port in ports) or "none detected"
            self.append_system_message(f"Port list refreshed: {devices}. AUTO or a manually entered port may be used.")

    def update_system_connection_controls(self, *, connected: bool | None = None, busy: bool | None = None) -> None:
        if connected is not None:
            self.system_connected = bool(connected)
        if busy is not None:
            self.system_busy = bool(busy)
        if hasattr(self, "advanced_buttons"):
            for button in self.advanced_buttons:
                button.setEnabled(self.system_connected and not self.system_busy)
        if hasattr(self, "start_scan_button"):
            self.update_run_controls()

        # ── Header instrument pills ─────────────────────────────────────────
        if hasattr(self, "global_status_banner"):
            if self.system_busy:
                self.global_status_banner.setText("● CONNECTING…")
                self.global_status_banner.setStyleSheet(
                    "font-size: 10px; font-weight: 700; color: #FEF3C7; background: #92400E;"
                    "border-radius: 10px; padding: 2px 10px;"
                )
            elif self.system_connected:
                port = getattr(self.connection_manager.getStatus(), "port", None) or self.selected_port() or "AUTO"
                self.global_status_banner.setText(f"● ONLINE · {port}")
                self.global_status_banner.setStyleSheet(
                    "font-size: 10px; font-weight: 700; color: #DCFCE7; background: #166534;"
                    "border-radius: 10px; padding: 2px 10px;"
                )
            else:
                self.global_status_banner.setText("● OFFLINE")
                self.global_status_banner.setStyleSheet(
                    "font-size: 10px; font-weight: 700; color: #FCA5A5; background: #7F1D1D;"
                    "border-radius: 10px; padding: 2px 10px;"
                )

        # ── Legacy connection_badge (left panel) ────────────────────────────
        if hasattr(self, "connection_badge"):
            if self.system_busy:
                self.connection_badge.setText("● CONNECTING / WORKING")
                self.connection_badge.setStyleSheet(
                    "font-weight: 800; color: #713F12; background: #FEF3C7;"
                    "border: 1px solid #D97706; padding: 8px; border-radius: 4px;"
                )
            elif self.system_connected:
                port = getattr(self.connection_manager.getStatus(), "port", None) or self.selected_port() or "AUTO"
                self.connection_badge.setText(f"● ONLINE · {port}")
                self.connection_badge.setStyleSheet(
                    "font-weight: 800; color: #14532D; background: #DCFCE7;"
                    "border: 1px solid #16A34A; padding: 8px; border-radius: 4px;"
                )
            else:
                self.connection_badge.setText("● OFFLINE")
                self.connection_badge.setStyleSheet(
                    "font-weight: 800; color: #7F1D1D; background: #FEE2E2;"
                    "border: 1px solid #DC2626; padding: 8px; border-radius: 4px;"
                )

        # ── Status bar ──────────────────────────────────────────────────────
        if hasattr(self, "_status_bar"):
            if self.system_busy:
                self._status_bar.showMessage("Connecting to hardware…")
            elif self.system_connected:
                auth = getattr(self, "motion_authorization", "LOCKED")
                self._status_bar.showMessage(
                    f"Connected · Motion: {auth} · Safety gate ARMED"
                )
            else:
                self._status_bar.showMessage("Offline — connect hardware or use simulation mode")

        if hasattr(self, "authorization_select"):
            self.update_authorization_controls()
        if not hasattr(self, "connect_button"):
            return

        if self.system_busy and not self.system_connected:
            self.connect_button.setText("Connecting...")
            self.connect_button.setStyleSheet(YELLOW_BUTTON_STYLE)
            self.connect_button.setEnabled(False)
            self.disconnect_button.setEnabled(False)
            self.disconnect_button.setStyleSheet(DISABLED_BUTTON_STYLE)
            return

        if self.system_busy and self.system_connected:
            self.connect_button.setText("Connected")
            self.connect_button.setStyleSheet(GREEN_BUTTON_STYLE)
            self.connect_button.setEnabled(False)
            self.disconnect_button.setEnabled(False)
            self.disconnect_button.setStyleSheet(DISABLED_BUTTON_STYLE)
            return

        if self.system_connected:
            self.connect_button.setText("Connected")
            self.connect_button.setStyleSheet(GREEN_BUTTON_STYLE)
            self.connect_button.setEnabled(False)
            self.disconnect_button.setEnabled(True)
            self.disconnect_button.setStyleSheet(RED_BUTTON_STYLE)
            return

        self.connect_button.setText("Connect Hardware")
        self.connect_button.setStyleSheet(YELLOW_BUTTON_STYLE)
        self.connect_button.setEnabled(True)
        self.disconnect_button.setEnabled(False)
        self.disconnect_button.setStyleSheet(DISABLED_BUTTON_STYLE)

    def run_worker(self, fn: Callable[[], dict[str, Any]], done: Callable[[dict[str, Any]], None]) -> bool:
        if self.worker and self.worker.isRunning():
            QMessageBox.warning(self, "Busy", "A hardware command is already running.")
            return False
        worker = Worker(fn)
        worker.finished_payload.connect(done)
        worker.finished_payload.connect(self.render_payload_log)
        worker.finished.connect(lambda: setattr(self, "worker", None))
        worker.finished.connect(lambda: self.update_system_connection_controls(busy=False))
        self.worker = worker
        worker.start()
        return True

    def connect_system(self) -> None:
        if self.system_connected:
            self.append_log("[SYSTEM] Already connected.")
            self.system_state.setText("System connected and ready.\nUse Disconnect or Safe Standby when finished.")
            self.append_system_message("Already connected. Diagnostics and Scan Control are available.")
            return
        port = self.selected_port()

        def action() -> dict[str, Any]:
            # Scan simulation and the physical connection are deliberately
            # independent. The main Connect button always targets MK4S.
            self.connection_manager.set_simulation_mode(False)
            return self.connection_manager.connect(port)

        self.update_system_connection_controls(connected=False, busy=True)
        self.system_state.setText("Connecting to the MK4S with a safe read-only handshake…")
        self.append_system_message(
            f"Starting the MK4S read-only handshake on {port or 'AUTO detection'}."
        )
        if not self.run_worker(action, self.render_system_payload):
            self.update_system_connection_controls(busy=False)

    def disconnect_system(self) -> None:
        self.update_system_connection_controls(busy=True)
        self.system_state.setText("Disconnecting safely...")
        self.append_system_message("Disconnect requested. Safe retract/standby state will be checked before disconnect.")
        if not self.run_worker(self.connection_manager.disconnect, self.render_system_payload):
            self.update_system_connection_controls(busy=False)

    def run_calibration(self) -> None:
        self.append_system_message(
            "Calibration blocked following unsafe Z homing. No command sent."
        )
        QMessageBox.warning(
            self, "Calibration Blocked",
            "Calibration is disabled after the Z homing incident.\n"
            "Arduino feedback and motion interlocks require verification."
        )

    def run_diagnosis(self) -> None:
        self.append_system_message("Diagnosis started: strictly read-only check (M115, M105, M119, M114). No motion.")
        self.run_worker(system_diagnostics, self.render_system_payload)

    def ai_error_correction(self) -> None:
        ports = discover_ports()
        message = str(self.last_system_payload.get("message", "") or "No failed handshake has been recorded yet.")
        lowered = message.casefold()
        recommendations: list[str] = []
        if not ports:
            recommendations.extend([
                "Reconnect the MK4S USB data cable directly to the PC; avoid charge-only cables and unpowered hubs.",
                "Open Windows Device Manager and confirm that a COM port appears when the printer is plugged in.",
                "Install/repair the Prusa USB serial driver if no COM device appears.",
            ])
        if any(token in lowered for token in ("access is denied", "permission", "busy", "in use")):
            recommendations.append("Close PrusaSlicer, serial terminals, OctoPrint bridges, and any previous SPM window using the same COM port.")
        if any(token in lowered for token in ("timeout", "incomplete", "not ready", "no response")):
            recommendations.extend([
                "Confirm the printer is powered, then press its reset button once and retry after five seconds.",
                "Select the detected COM port explicitly instead of AUTO and retry the read-only handshake.",
                "Verify 115200 baud and inspect whether M115, M105, M119, and M114 each return an `ok` response.",
            ])
        if "no prusa" in lowered or "not found" in lowered:
            recommendations.append("Use Refresh Ports, select the newly detected COM device, and retry with the printer powered on.")
        if not recommendations:
            recommendations.extend([
                "Refresh ports and select the MK4S COM port explicitly.",
                "Retry the safe read-only handshake; it sends only M115, M105, M119, and M114.",
                "If it fails again, copy this report together with the developer log paths shown below.",
            ])
        port_lines = [f"- {port.device}: {port.description or 'no description'} [{port.hardware_id or 'no HWID'}]" for port in ports]
        report = "\n".join([
            "AI-GUIDED MK4S CONNECTION REPORT",
            "",
            f"UI state: {'connected' if self.system_connected else 'offline'}",
            f"Selected port: {self.selected_port() or 'AUTO'}",
            f"Last result: {message}",
            f"Read-only gate: {os.getenv('SPM_WEB_ALLOW_READONLY_HARDWARE', '0')}",
            f"Motion authorization: {self.motion_authorization}",
            "",
            "Detected serial devices:",
            *(port_lines or ["- none"]),
            "",
            "Recommended recovery:",
            *[f"{index}. {item}" for index, item in enumerate(recommendations, 1)],
            "",
            f"Text log: {self.last_system_payload.get('dev_log_file', 'not generated')}",
            f"JSONL log: {self.last_system_payload.get('dev_log_jsonl', 'not generated')}",
            "",
            "Safety: troubleshooting does not enable motion or transmit movement commands.",
        ])
        dialog = QMessageBox(self)
        dialog.setWindowTitle("AI Connection Assistant")
        dialog.setIcon(QMessageBox.Icon.Information)
        dialog.setText("MK4S connection analysis is ready.")
        dialog.setInformativeText("Review the detected ports and recovery plan below.")
        dialog.setDetailedText(report)
        retry_button = dialog.addButton("Refresh && Retry", QMessageBox.ButtonRole.ActionRole)
        copy_button = dialog.addButton("Copy Report", QMessageBox.ButtonRole.ActionRole)
        dialog.addButton(QMessageBox.StandardButton.Close)
        dialog.exec()
        self.append_log("[CONNECTION ASSISTANT] Generated hardware-safe troubleshooting report.")
        if dialog.clickedButton() is copy_button:
            QApplication.clipboard().setText(report)
            self.append_system_message("Connection troubleshooting report copied to clipboard.")
        elif dialog.clickedButton() is retry_button:
            self.refresh_ports()
            self.connect_system()

    def safe_standby(self) -> None:
        if QMessageBox.question(self, "Safe Standby", "Move to X125 Y105 Z120?") != QMessageBox.StandardButton.Yes:
            return
        self.append_system_message("Safe Standby requested: X125 Y105 Z120.")
        self.run_worker(system_safe_standby, self.render_system_payload)

    def load_z_reference(self) -> None:
        payload = z_reference_payload()
        surface_z = float(payload["surface_z_mm"])
        safe_min_z = float(payload["safe_min_z_mm"])
        self.target_z.setValue(safe_min_z)
        self.contact_limit.setValue(safe_min_z)
        self.expected_surface_z.setValue(surface_z)
        self.z_state.setText(
            f"Z reference: surface {surface_z:.3f} mm, safe minimum {safe_min_z:.3f} mm"
        )

    def read_z(self) -> None:
        self.run_worker(lambda: z_read_status(port=self.selected_port() or None), self.render_z_payload)

    def current_approach_advice(self) -> dict[str, object]:
        return advise_approach(
            ApproachAdvisorInput(
                z_setpoint_mm=float(self.target_z.value()),
                tapping_range_mm=float(self.tapping_range.value()),
                expected_surface_z_mm=float(self.expected_surface_z.value()),
                approach_speed_mm_s=float(self.approach_speed.value()),
                full_retract_z_mm=float(self.full_retract_z.value()),
                latest_z_mm=float(self.latest_z_value),
                connected=bool(self.system_connected),
            )
        )

    def run_approach_advisor(self) -> None:
        advice = self.current_approach_advice()
        issue_lines = [f"- {item}" for item in advice["issues"]] if advice["issues"] else ["- none"]
        recommendation_lines = [f"- {item}" for item in advice["recommendations"]]
        lines = [
            str(advice["summary"]),
            "",
            "Issues:",
            *issue_lines,
            "",
            "Recommendations:",
            *recommendation_lines,
        ]
        text = "\n".join(lines)
        self.z_state.setText(text)
        self.append_log(f"[APPROACH ADVISOR] {advice['summary']}")
        QMessageBox.information(self, "Approach Advisor", text)

    def apply_target_z(self) -> None:
        target = float(self.target_z.value())
        if self.simulation_engine.is_active:
            x, y, _z = self.simulation_engine.scanner_position
            self.simulation_engine.scanner.set_position(x, y, target)
            self.render_virtual_position(self.simulation_engine.move_to_position(x, y, target, dt=0.05), "APPROACH")
            return
        if QMessageBox.question(
            self,
            "Manual Approach to Setpoint",
            f"Move Z directly to setpoint {target:.3f} mm without feedback?",
        ) != QMessageBox.StandardButton.Yes:
            return
        if self.worker and self.worker.isRunning():
            QMessageBox.warning(self, "Busy", "A hardware command is already running.")
            return
        worker = ZSetpointWorker(target)
        worker.sample.connect(self.render_z_sample)
        worker.finished_payload.connect(self.render_z_payload)
        worker.finished_payload.connect(self.render_payload_log)
        worker.finished.connect(lambda: setattr(self, "worker", None))
        self.worker = worker
        worker.start()

    def auto_approach_z(self) -> None:
        setpoint = float(self.target_z.value())
        tapping_range = float(self.tapping_range.value())
        approach_speed = float(self.approach_speed.value())
        if self.simulation_engine.is_active:
            x, y, _z = self.simulation_engine.scanner_position
            surface = self.simulation_engine.current_sample.get_height_at_position(x, y)
            target = setpoint + surface
            self.simulation_engine.scanner.set_position(x, y, target)
            self.render_virtual_position(self.simulation_engine.move_to_position(x, y, target, dt=0.05), "AUTO APPROACH")
            return
        if QMessageBox.question(
            self,
            "Auto Approach Simulation",
            (
                f"Simulate feedback approach through {tapping_range:.3f} mm down to "
                f"Z setpoint {setpoint:.3f} mm at {approach_speed:.3f} mm/s?\n\n"
                "Real sensor-based approach is disabled until the feedback sensor is verified."
            ),
        ) != QMessageBox.StandardButton.Yes:
            return
        worker = ZAutoApproachSimulationWorker(
            start_z=self.latest_z_value,
            surface_z=setpoint,
            clearance=0.0,
        )
        worker.sample.connect(self.render_z_sample)
        worker.finished_payload.connect(self.render_z_payload)
        worker.finished_payload.connect(self.render_payload_log)
        worker.finished.connect(lambda: setattr(self, "worker", None))
        self.worker = worker
        worker.start()

    def retract_z(self) -> None:
        if self.simulation_engine.is_active:
            x, y, _z = self.simulation_engine.scanner_position
            target = float(self.full_retract_z.value())
            self.simulation_engine.scanner.set_position(x, y, target)
            self.render_virtual_position(self.simulation_engine.move_to_position(x, y, target, dt=0.05), "RETRACT")
            return
        if QMessageBox.question(self, "Retract Z", "Retract Z to the configured safe height?") != QMessageBox.StandardButton.Yes:
            return
        self.run_worker(lambda: z_retract(confirmed=True), self.render_z_payload)

    def stop_z(self) -> None:
        from core.system.deterministic_safety_gate import HARDWARE_SAFETY_GATE
        from core.system.safety_supervisor import SAFETY_SUPERVISOR

        request_real_scan_stop()
        try:
            HARDWARE_SAFETY_GATE.emergency_stop("Operator Workstation Stop Button Clicked")
        except Exception:
            pass
        try:
            SAFETY_SUPERVISOR.emergency_stop("Operator Workstation Stop Button Clicked")
        except Exception:
            pass

        if self.simulation_engine.is_active:
            self.simulation_engine.stop_scan()
            self.measurement_timer.stop()
            self.append_log("[SIMULATION] Virtual Z/scan stop completed; safety gates latched E_STOP.")
            if self.z_scanner_window is not None:
                self.z_scanner_window.update_instrument_state(
                    connected=self.system_connected, motion_enabled=False, acquisition="Simulation Stopped"
                )
            return
        payload = z_stop_now()
        self.render_z_payload(payload)
        self.render_payload_log(payload)

    def render_virtual_position(self, sample: dict[str, float], phase: str) -> None:
        z_value = float(sample["z"])
        self.latest_z_value = z_value
        self.z_trace.add_sample(z_value)
        self.current_z.setText(f"Current Z: {z_value:.3f} mm")
        self.count_z.setText(f"Count Z: {int(round(z_value * 400.0))}")
        self.deflection.setText(f"Deflection: {float(sample['deflection']):.5f}")
        self.clearance.setText(f"Virtual surface: {float(sample['surface_height']):.4f} mm")
        self.z_state.setText(
            f"Simulation {phase}: X={float(sample['x']):.3f} Y={float(sample['y']):.3f} Z={z_value:.3f} mm"
        )
        self.append_log(f"[SIMULATION] {phase} completed at Z {z_value:.3f} mm; no hardware command sent.")

    def render_system_payload(self, payload: dict[str, Any]) -> None:
        self.last_system_payload = dict(payload)
        status = str(payload.get("status", ""))
        if status == "disconnected":
            connected = False
        elif any(key in payload for key in ("connected", "powered", "system_powered")):
            connected = bool(payload.get("connected") or payload.get("powered") or payload.get("system_powered"))
        else:
            # Diagnostics, calibration, and motion-result payloads do not all
            # repeat lifecycle fields. They must not silently tear down a live
            # connection in the desktop UI.
            connected = self.system_connected
        self.update_system_connection_controls(connected=connected, busy=False)
        position = payload.get("position") or (payload.get("hardware") or {}).get("position") or ""
        if connected:
            self.system_state.setText(
                "CONNECTION VERIFIED\n"
                f"Device: {payload.get('machine_type') or 'Prusa MK4S'}\n"
                f"Port: {payload.get('port', '') or 'AUTO'} · Read-only safety handshake\n"
                f"Firmware: {payload.get('firmware', '') or 'reported by M115'}\n"
                f"Temperature: {payload.get('temperature', '') or 'reported by M105'}\n"
                f"Position: {position or 'reported by M114'}\n"
                "Safety: no movement, homing, heating, or writes during connection"
            )
        else:
            self.system_state.setText(
                "CONNECTION NOT READY\n"
                f"Port: {payload.get('port', '') or self.selected_port() or 'AUTO'}\n"
                f"Reason: {payload.get('message', '') or payload.get('status', 'Unknown failure')}\n\n"
                "Use Refresh Ports, select the detected MK4S port, then retry. "
                "Open AI Connection Assistant for a detailed recovery report."
            )
        if hasattr(self, "overview_status"):
            self.overview_status.setText(
                f"Status: {'Connected' if connected else payload.get('status', 'Disconnected')}\n"
                f"Device: {payload.get('machine_type', 'MK4S')}\nPort: {payload.get('port', '') or '—'}\n"
                f"Mode: {payload.get('mode', 'read-only')}\nMotion authorization: "
                f"{'Enabled' if os.getenv('SPM_WEB_ALLOW_HEALTH_MOTION', '0') == '1' else 'Disabled'}"
            )
        if self.z_scanner_window is not None:
            self.z_scanner_window.update_instrument_state(
                connected=connected,
                motion_enabled=os.getenv("SPM_WEB_ALLOW_REAL_SCAN", "0") == "1",
            )
        message = str(payload.get("message", "") or payload.get("status", ""))
        if connected:
            self.append_system_message(f"Connected on {payload.get('port', '') or 'selected port'}. Diagnostics and Scan Control are ready.")
        elif payload.get("status") == "disconnected":
            self.append_system_message("Disconnected. It is safe to connect again or close the software.")
            if self.motion_authorization != "LOCKED":
                self.authorization_select.blockSignals(True)
                self.authorization_select.setCurrentText("LOCKED")
                self.authorization_select.blockSignals(False)
                self.apply_motion_authorization("LOCKED", confirm=False)
        elif payload.get("ok") is False:
            self.append_system_message(f"Action blocked or failed: {message}")
        elif message:
            self.append_system_message(message)

    def render_z_sample(self, sample: dict[str, Any]) -> None:
        z_value = sample.get("z")
        if z_value is None:
            return
        self.z_trace.add_sample(float(z_value))
        self.latest_z_value = float(z_value)
        self.current_z.setText(f"Current Z: {float(z_value):.3f} mm")
        self.z_state.setText(f"Live setpoint move: {sample.get('phase')} Z={float(z_value):.3f} target={sample.get('target_z')}")
        self.append_log(f"[Z POINT] {sample.get('phase')} Z={float(z_value):.3f} target={sample.get('target_z')}")

    def render_measurement_point(self, point: dict[str, Any]) -> None:
        line_index = int(point.get("line_index", 0))
        while len(self.measurement_lines) < line_index:
            self.measurement_lines.append([])
        if line_index != self.measurement_line_index:
            if self.measurement_current_line:
                self.measurement_lines.append(self.measurement_current_line)
            self.measurement_current_line = []
            self.measurement_line_index = line_index
        self.measurement_current_line.append(dict(point))
        z_value = float(point["z_feedback"])
        self.latest_z_value = z_value
        self.z_trace.add_sample(z_value)
        self.current_z.setText(f"Current Z: {z_value:.3f} mm")
        self.z_state.setText(
            f"Real scan: line {line_index + 1}, point {int(point.get('point_index', 0)) + 1}, "
            f"X={float(point['x']):.3f} Y={float(point['y']):.3f} Z={z_value:.3f} mm"
        )
        self.append_log(
            f"[REAL SCAN POINT] line={line_index + 1} point={int(point.get('point_index', 0)) + 1} "
            f"X={float(point['x']):.3f} Y={float(point['y']):.3f} Z={z_value:.3f}"
        )
        if self.z_scanner_window is not None and self.measurement_profile is not None:
            point_index = int(point.get("point_index", 0))
            total = max(1, self.measurement_profile.x_points * self.measurement_profile.y_points)
            completed = line_index * self.measurement_profile.x_points + point_index + 1
            self.z_scanner_window.scan_progress.setValue(min(100, max(1, int(completed * 100 / total))))
            self.z_scanner_window.scan_progress.setFormat("Acquiring · %p%")
            self.z_scanner_window.point_readout.setText(
                f"Line {line_index + 1} / {self.measurement_profile.y_points} · "
                f"Point {point_index + 1} / {self.measurement_profile.x_points} · "
                f"X {float(point['x']):.3f} · Y {float(point['y']):.3f}"
            )
            self.z_scanner_window.update_instrument_state(
                connected=self.system_connected, motion_enabled=True, acquisition="Running"
            )
        self.refresh_signal_windows()

    def render_z_payload(self, payload: dict[str, Any]) -> None:
        current = payload.get("current") or {}
        if current.get("z") is not None:
            z_value = float(current["z"])
            self.latest_z_value = z_value
            self.z_trace.add_sample(z_value)
            self.current_z.setText(f"Current Z: {z_value:.3f} mm")
        if current.get("count_z") is not None:
            self.count_z.setText(f"Count Z: {int(current['count_z'])}")
        if payload.get("clearance_um") is not None:
            self.clearance.setText(f"Clearance: {float(payload['clearance_um']):.1f} um")
        probe = payload.get("probe") or {}
        if probe.get("connected"):
            is_triggered = bool(probe.get("triggered") or probe.get("trigger_raw") or probe.get("trigger_latched"))
            status_text = "CONTACT" if is_triggered else "OPEN"
            d3_val = int(bool(probe.get("trigger_raw")))
            latched_val = int(bool(probe.get("trigger_latched")))
            edges = probe.get("edges", 0)
            self.deflection.setText(f"Deflection: {status_text} (D3={d3_val}, latched={latched_val}, edges={edges})")
            self.deflection.setStyleSheet(
                "border: 2px solid #dc2626; padding: 8px; background: #fee2e2; color: #7f1d1d; font-weight: 800;"
                if is_triggered else
                "border: 2px solid #16a34a; padding: 8px; background: #dcfce7; color: #14532d; font-weight: 800;"
            )
        elif "error" in probe:
            self.deflection.setText(f"Deflection: Arduino offline")
            self.deflection.setStyleSheet("border: 1px solid #d97706; padding: 8px; background: #fef3c7; color: #92400e;")
        self.z_state.setText(f"ok={payload.get('ok')} status={payload.get('status')}\n{payload.get('message', '')}")

    def render_payload_log(self, payload: dict[str, Any]) -> None:
        for line in payload.get("log_lines") or [payload.get("message", "")]:
            self.append_log(str(line))

    def append_log(self, message: str) -> None:
        if message:
            timestamp = f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] "
            entry = f"{timestamp if not hasattr(self, 'show_timestamps') or self.show_timestamps.isChecked() else ''}{message}"
            if hasattr(self, "log"):
                self.log.append(entry)
            if hasattr(self, "main_log"):
                self.main_log.append(entry)
                lowered = message.lower()
                lane = "errors" if any(token in lowered for token in ("error", "failed", "blocked")) else (
                    "warnings" if any(token in lowered for token in ("warning", "lockout", "unsafe")) else "events"
                )
                if hasattr(self, "severity_logs"):
                    self.severity_logs[lane].append(entry)
                if getattr(self, "auto_scroll", None) and self.auto_scroll.isChecked():
                    self.main_log.ensureCursorVisible()

    def append_system_message(self, message: str) -> None:
        if message and hasattr(self, "system_log"):
            self.system_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")

    def clear_log(self) -> None:
        if hasattr(self, "log"):
            self.log.clear()
        if hasattr(self, "main_log"):
            self.main_log.clear()
        self.append_log("Live log cleared.")

    def download_log(self) -> None:
        default = PROJECT_ROOT / "logs" / f"spm_operator_software_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        default.parent.mkdir(parents=True, exist_ok=True)
        path, _ = QFileDialog.getSaveFileName(self, "Download Live Log", str(default), "Text files (*.txt);;All files (*)")
        if not path:
            return
        source = self.main_log if hasattr(self, "main_log") else self.log
        Path(path).write_text(source.toPlainText(), encoding="utf-8")
        self.append_log(f"Live log saved: {path}")

    def show_about(self) -> None:
        QMessageBox.information(
            self,
            "About",
            "SPM Operator Interface\n"
            f"Version: {FULL_VERSION}\n"
            f"Build Date: {BUILD_DATE_DISPLAY}\n"
            f"Build: {git_build_id(PROJECT_ROOT)}\n\n"
            "Copyright © 2026",
        )

    def open_z_scanner_window(self) -> None:
        if hasattr(self, "center_tabs") and self.z_scanner_window is not None:
            self.center_tabs.setCurrentWidget(self.z_scanner_window)
        if self.z_scanner_window is not None:
            self.z_scanner_window.show()
            self.z_scanner_window.raise_()
            self.z_scanner_window.activateWindow()

    def open_measurement_window(self) -> None:
        if self.measurement_window is not None:
            self.measurement_window.show()
            self.measurement_window.raise_()
            self.measurement_window.activateWindow()

    def open_live_log_window(self) -> None:
        if self.live_log_window is not None:
            self.live_log_window.show()
            self.live_log_window.raise_()
            self.live_log_window.activateWindow()

    def open_academic_gcode_window(self) -> None:
        if hasattr(self, "center_tabs") and self.academic_gcode_window is not None:
            self.center_tabs.setCurrentWidget(self.academic_gcode_window)
        if self.academic_gcode_window is not None:
            self.academic_gcode_window.show()
            self.academic_gcode_window.raise_()
            self.academic_gcode_window.activateWindow()

    def open_crtouch_prep_window(self) -> None:
        if hasattr(self, "center_tabs") and self.crtouch_prep_window is not None:
            self.center_tabs.setCurrentWidget(self.crtouch_prep_window)
        if self.crtouch_prep_window is not None:
            self.crtouch_prep_window.show()
            self.crtouch_prep_window.raise_()
            self.crtouch_prep_window.activateWindow()

    def open_signal_window(self, mode: str, direction: str) -> None:
        key = f"{mode}:{direction}"
        if key not in self.signal_windows:
            dialog = QDialog(self)
            title = f"{'Line Mode' if mode == 'line' else 'Topography'} {direction}"
            dialog.setWindowTitle(title)
            dialog.resize(760, 460)
            layout = QVBoxLayout()
            plot = SignalPlotWidget(title=title, mode=mode, direction=direction)
            layout.addWidget(plot)
            dialog.setLayout(layout)
            self.signal_windows[key] = dialog
            self.signal_plots[key] = plot
        self.refresh_signal_windows()
        self.signal_windows[key].show()
        self.signal_windows[key].raise_()
        self.signal_windows[key].activateWindow()

    def open_all_signal_windows(self) -> None:
        for mode in ("line", "topography"):
            for direction in ("X+", "X-", "Y+", "Y-"):
                self.open_signal_window(mode, direction)

    def start_measurement_simulation(
        self,
        profile: WebScanProfile,
        scan_speed_mm_s: float,
        *,
        dry_run: bool = False,
    ) -> bool:
        try:
            profile.validate()
        except ValueError as exc:
            QMessageBox.warning(self, "Measurement profile invalid", str(exc))
            return False
        self.measurement_timer.stop()
        self.measurement_profile = profile
        self.measurement_lines = []
        self.measurement_current_line = []
        if not self.simulation_engine.is_active:
            self.simulation_engine.enable(self.simulation_sample_type, self.simulation_sample_params)
        self.simulation_engine.start_scan(
            {"x_min": profile.x_min, "x_max": profile.x_max, "y_min": profile.y_min, "y_max": profile.y_max,
             "x_points": profile.x_points, "y_points": profile.y_points}
        )
        self.measurement_line_payload = self.build_virtual_scan_line(profile, 0)
        self.measurement_line_index = 0
        self.measurement_point_index = 0
        self.measurement_paused = False
        display_rate = "Fast"
        if self.z_scanner_window is not None:
            display_rate = self.z_scanner_window.speed_profile.currentText()
        timing = {
            "Synchronized": (1, max(8, int(1000.0 / max(1.0, scan_speed_mm_s * 20.0)))),
            "Fast": (8, 16),
            "Extreme": (32, 8),
        }
        self.measurement_batch_size, interval_ms = timing.get(display_rate, timing["Fast"])
        self.measurement_timer.start(interval_ms)
        acquisition = "Dry Run" if dry_run else "Simulation"
        self.append_log(
            f"[{acquisition.upper()}] Scan started: {profile.x_points} points x {profile.y_points} lines, "
            f"speed {scan_speed_mm_s:.2f} mm/s, display {display_rate}; no G-code will be sent"
        )
        if self.z_scanner_window is not None:
            self.z_scanner_window.scan_progress.setValue(0)
            self.z_scanner_window.scan_progress.setFormat(f"{acquisition} · %p%")
            self.z_scanner_window.update_instrument_state(
                connected=self.system_connected,
                motion_enabled=False,
                acquisition=acquisition,
            )
        self.refresh_signal_windows()
        return True

    def build_virtual_scan_line(self, profile: WebScanProfile, line_index: int) -> dict[str, Any]:
        coordinates, direction = raster_line_coordinates(profile, line_index)
        points = []
        for point_index, (x, y) in enumerate(coordinates):
            signals = self.simulation_engine.scan_point(x, y, z_setpoint=profile.z_setpoint, dt=0.01)
            points.append(
                {
                    "point_index": point_index,
                    "line_index": line_index,
                    "x": round(x, 6),
                    "y": round(y, 6),
                    "surface_height": round(signals["surface_height"], 6),
                    "z_feedback": round(signals["z"], 6),
                    "feedback_error": round(signals["error"], 6),
                    "deflection": round(signals["deflection"], 6),
                    "amplitude": round(signals["amplitude"], 6),
                    "current": round(signals["current"], 6),
                    "z_correction": round(signals["z_correction"], 6),
                }
            )
        return {"line_index": line_index, "line_count": profile.y_points, "direction": direction, "points": points}

    def pause_measurement(self) -> None:
        self.measurement_paused = not self.measurement_paused
        if self.measurement_paused:
            request_real_scan_pause()
        else:
            clear_real_scan_pause()
        self.append_log(f"[MEASUREMENT] {'Paused' if self.measurement_paused else 'Resumed'}")

    def stop_measurement(self) -> None:
        self.measurement_timer.stop()
        if self.simulation_engine.is_active:
            self.simulation_engine.stop_scan()
        self.measurement_paused = False
        clear_real_scan_pause()
        request_real_scan_stop()
        self.append_log("[MEASUREMENT] Stopped")
        if self.z_scanner_window is not None:
            self.z_scanner_window.update_instrument_state(
                connected=self.system_connected,
                motion_enabled=os.getenv("SPM_WEB_ALLOW_REAL_SCAN", "0") == "1",
                acquisition="Stopped",
            )
            self.z_scanner_window.scan_progress.setFormat("Stopped · %p%")

    def start_measurement_real_scan(self, profile: WebScanProfile, scan_speed_mm_s: float) -> bool:
        try:
            profile.validate()
        except ValueError as exc:
            QMessageBox.warning(self, "Measurement profile invalid", str(exc))
            return False
        if QMessageBox.question(
            self,
            "Start Constant-Z Raster",
            (
                f"Move real MK4S hardware through {profile.x_points} x {profile.y_points} points "
                f"over X {profile.x_min:.1f}..{profile.x_max:.1f} mm and "
                f"Y {profile.y_min:.1f}..{profile.y_max:.1f} mm at Z {profile.z_setpoint:.3f} mm?\n\n"
                "This is an XY raster with M114 Z readback. It does not approach/tap the foil. "
                "For feature-touching height measurement use Start Tapping Scan 50x50."
            ),
        ) != QMessageBox.StandardButton.Yes:
            return False
        if self.worker and self.worker.isRunning():
            QMessageBox.warning(self, "Busy", "A hardware command is already running.")
            return False
        self.measurement_timer.stop()
        self.measurement_profile = profile
        self.measurement_lines = []
        self.measurement_current_line = []
        self.measurement_line_index = 0
        self.measurement_point_index = 0
        self.measurement_paused = False
        clear_real_scan_pause()
        worker = RealScanWorker(profile, scan_speed_mm_s, self.selected_port() or None)
        worker.point.connect(self.render_measurement_point)
        worker.finished_payload.connect(self.render_real_scan_payload)
        worker.finished_payload.connect(self.render_payload_log)
        worker.finished.connect(lambda: setattr(self, "worker", None))
        self.worker = worker
        self.append_log(
            f"[REAL SCAN] Requested: {profile.x_points} points x {profile.y_points} lines, "
            f"X {profile.x_min:.1f}..{profile.x_max:.1f}, Y {profile.y_min:.1f}..{profile.y_max:.1f}, "
            f"Z {profile.z_setpoint:.3f}"
        )
        self.refresh_signal_windows()
        worker.start()
        return True

    def start_measurement_hardware_dry_run(self, profile: WebScanProfile, scan_speed_mm_s: float) -> bool:
        if not self.system_connected:
            QMessageBox.warning(self, "Hardware Required for Dry Run", "Hardware required for Dry Run. Connect and verify the MK4S + CRTouch first.")
            return False
        if self.motion_authorization != "OPERATIONAL":
            QMessageBox.warning(self, "Dry Run Locked", "Select OPERATIONAL authorization before Hardware Dry Run.")
            return False
        if os.getenv("SPM_ALLOW_HARDWARE_DRY_RUN", "0").strip().lower() not in {"1", "true", "yes"}:
            QMessageBox.warning(
                self,
                "Hardware Dry Run Locked",
                "Hardware Dry Run requires explicit launch authorization: SPM_ALLOW_HARDWARE_DRY_RUN=1.",
            )
            return False
        try:
            profile.validate()
        except ValueError as exc:
            QMessageBox.warning(self, "Dry Run profile invalid", str(exc))
            return False
        if self.worker and self.worker.isRunning():
            QMessageBox.warning(self, "Busy", "A hardware command is already running.")
            return False
        if QMessageBox.question(
            self,
            "Start Hardware Dry Run",
            (
                f"Move the real MK4S through {profile.x_points} x {profile.y_points} points at "
                f"{scan_speed_mm_s:.2f} mm/s while Z follows the {self.simulation_sample_label(self.simulation_sample_type)} virtual profile?\n\n"
                "CRTouch/M114 values will come from hardware. The scanner will retract and home XY when finished. No physical sample is required."
            ),
        ) != QMessageBox.StandardButton.Yes:
            return False
        self.simulation_engine.disable()
        self.measurement_timer.stop()
        self.measurement_profile = profile
        self.measurement_lines = []
        self.measurement_current_line = []
        self.measurement_line_index = 0
        self.measurement_point_index = 0
        worker = HardwareDryRunWorker(
            profile,
            self.simulation_sample_type,
            self.simulation_sample_params,
            scan_speed_mm_s,
            self.selected_port() or None,
        )
        worker.point.connect(self.render_measurement_point)
        worker.finished_payload.connect(self.render_real_scan_payload)
        worker.finished_payload.connect(self.render_payload_log)
        worker.finished.connect(lambda: setattr(self, "worker", None))
        self.worker = worker
        self.append_log(
            f"[HARDWARE DRY RUN] Real motion requested: {profile.x_points} x {profile.y_points}; "
            f"sample={self.simulation_sample_type}; speed={scan_speed_mm_s:.2f} mm/s."
        )
        worker.start()
        return True

    def start_measurement_foil_tap_scan(
        self,
        profile: WebScanProfile,
        tap_config: FoilTapConfig,
        scan_speed_mm_s: float,
    ) -> bool:
        try:
            profile.validate()
        except ValueError as exc:
            QMessageBox.warning(self, "Foil tap profile invalid", str(exc))
            return False
        reference = z_reference_payload()
        safe_min_z = float(reference["safe_min_z_mm"])
        if tap_config.tap_min_z_mm < safe_min_z:
            QMessageBox.critical(
                self,
                "Unsafe Z Contact Limit",
                (
                    f"Hardware scan blocked: contact limit Z {tap_config.tap_min_z_mm:.3f} mm is below "
                    f"the confirmed safe minimum Z {safe_min_z:.3f} mm.\n\n"
                    "Reload the confirmed Z reference or raise the contact limit."
                ),
            )
            return False
        approach_advice = self.current_approach_advice()
        if approach_advice["risk"] == "blocked":
            message = "\n".join(
                [
                    str(approach_advice["summary"]),
                    "",
                    "Fix before tapping scan:",
                    *[f"- {item}" for item in approach_advice["recommendations"]],
                ]
            )
            self.z_state.setText(message)
            QMessageBox.warning(self, "Approach Advisor Blocked Scan", message)
            return False
        expected_surface = float(self.expected_surface_z.value())
        if tap_config.tap_min_z_mm >= expected_surface and expected_surface > 0:
            QMessageBox.warning(
                self,
                "Z Search Window Cannot Reach Surface",
                (
                    f"The configured search stops at Z {tap_config.tap_min_z_mm:.3f} mm, "
                    f"but the expected surface is around Z {expected_surface:.3f} mm.\n\n"
                    "The scanner would stop above the sample and report no contact. "
                    "Lower the Z setpoint/search limit below the expected surface height."
                ),
            )
            return False
        if QMessageBox.question(
            self,
            "Start Foil Tap Scan",
            (
                f"Run experimental tapping scan over 50 x 50 mm, {profile.x_points} x {profile.y_points} points?\n\n"
                f"Search window: Z {tap_config.tap_start_z_mm:.3f} down to {tap_config.tap_min_z_mm:.3f} mm, "
                f"full retract to Z {tap_config.full_retract_z_mm:.3f} after each point.\n\n"
                "Sequence: move XY -> approach until contact -> record contact Z -> retract -> next point. "
                "This uses experimental M119 z_min contact detection. Watch hardware continuously."
            ),
        ) != QMessageBox.StandardButton.Yes:
            return False
        if self.worker and self.worker.isRunning():
            QMessageBox.warning(self, "Busy", "A hardware command is already running.")
            return False
        self.measurement_timer.stop()
        self.measurement_profile = profile
        self.measurement_lines = []
        self.measurement_current_line = []
        self.measurement_line_index = 0
        self.measurement_point_index = 0
        self.measurement_paused = False
        clear_real_scan_pause()
        worker = FoilTapScanWorker(profile, tap_config, scan_speed_mm_s, self.selected_port() or None)
        worker.point.connect(self.render_measurement_point)
        worker.finished_payload.connect(self.render_real_scan_payload)
        worker.finished_payload.connect(self.render_payload_log)
        worker.finished.connect(lambda: setattr(self, "worker", None))
        self.worker = worker
        self.append_log(
            f"[TAPPING SCAN] Requested: {profile.x_points} x {profile.y_points}, "
            f"X {profile.x_min:.1f}..{profile.x_max:.1f}, Y {profile.y_min:.1f}..{profile.y_max:.1f}, "
            f"search Z {tap_config.tap_start_z_mm:.3f}->{tap_config.tap_min_z_mm:.3f}, "
            f"expected surface Z {float(self.expected_surface_z.value()):.3f}, full retract Z {tap_config.full_retract_z_mm:.3f}"
        )
        self.refresh_signal_windows()
        worker.start()
        return True

    def render_real_scan_payload(self, payload: dict[str, Any]) -> None:
        if self.measurement_current_line:
            self.measurement_lines.append(self.measurement_current_line)
            self.measurement_current_line = []
        self.refresh_signal_windows()
        if self.measurement_window is not None:
            self.measurement_window.status.setText(
                f"Real scan status: ok={payload.get('ok')} {payload.get('status')} - {payload.get('message', '')}"
            )
        self.z_state.setText(f"Real scan: ok={payload.get('ok')} status={payload.get('status')}\n{payload.get('message', '')}")

    def advance_measurement_batch(self) -> None:
        """Consume one synchronized acquisition batch and repaint all channels once."""
        changed = False
        for _ in range(max(1, self.measurement_batch_size)):
            if not self.advance_measurement_point(refresh=False):
                break
            changed = True
        if changed:
            self.refresh_signal_windows()

    def advance_measurement_point(self, *, refresh: bool = True) -> bool:
        if self.measurement_paused or self.measurement_profile is None or self.measurement_line_payload is None:
            return False
        points = self.measurement_line_payload["points"]
        if self.measurement_point_index >= len(points):
            if self.measurement_current_line:
                self.measurement_lines.append(self.measurement_current_line)
                self.measurement_current_line = []
            self.measurement_line_index += 1
            if self.measurement_line_index >= self.measurement_profile.y_points:
                self.measurement_timer.stop()
                self.append_log("[MEASUREMENT] Simulated scan complete")
                self.refresh_signal_windows()
                if self.z_scanner_window is not None:
                    self.z_scanner_window.scan_progress.setValue(100)
                    self.z_scanner_window.scan_progress.setFormat("Complete · %p%")
                    self.z_scanner_window.update_instrument_state(
                        connected=self.system_connected,
                        motion_enabled=False,
                        acquisition="Complete",
                    )
                return False
            self.measurement_line_payload = self.build_virtual_scan_line(self.measurement_profile, self.measurement_line_index)
            self.measurement_point_index = 0
            points = self.measurement_line_payload["points"]

        point = dict(points[self.measurement_point_index])
        self.measurement_point_index += 1
        self.measurement_current_line.append(point)
        z_value = float(point["z_feedback"])
        self.latest_z_value = z_value
        self.z_trace.add_sample(z_value)
        self.current_z.setText(f"Current Z: {z_value:.3f} mm")
        self.count_z.setText(f"Count Z: {int(round(z_value * 400.0))}")
        self.clearance.setText(f"Clearance: {float(point['surface_height']) * 1000.0:.1f} µm virtual height")
        self.deflection.setText(f"Deflection: {float(point.get('deflection', 0.0)):.5f}")
        self.z_state.setText(
            f"Measurement simulation: line {self.measurement_line_index + 1}/{self.measurement_profile.y_points}, "
            f"point {self.measurement_point_index}/{self.measurement_profile.x_points}, Z={z_value:.4f} mm"
        )
        if self.z_scanner_window is not None:
            total = max(1, self.measurement_profile.x_points * self.measurement_profile.y_points)
            completed = self.measurement_line_index * self.measurement_profile.x_points + self.measurement_point_index
            self.z_scanner_window.scan_progress.setValue(min(100, max(1, int(completed * 100 / total))))
            self.z_scanner_window.point_readout.setText(
                f"Line {self.measurement_line_index + 1} / {self.measurement_profile.y_points} · "
                f"Point {self.measurement_point_index} / {self.measurement_profile.x_points} · "
                f"X {float(point['x']):.3f} · Y {float(point['y']):.3f} · Z {z_value:.4f}"
            )
        if refresh:
            self.refresh_signal_windows()
        return True

    def refresh_signal_windows(self) -> None:
        if self.measurement_window is not None:
            self.measurement_window.update_progress_views(self.measurement_lines, self.measurement_current_line)
        for plot in self.signal_plots.values():
            plot.set_scan_data(self.measurement_lines, self.measurement_current_line)


def main() -> int:
    app = QApplication(sys.argv)
    window = OperatorWorkstation()
    window.showMaximized()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
