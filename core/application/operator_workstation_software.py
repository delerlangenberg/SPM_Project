from __future__ import annotations

import os
import sys
import math
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from PyQt5.QtCore import QThread, QTimer, Qt, pyqtSignal
from PyQt5.QtGui import QColor, QPainter, QPen
from PyQt5.QtWidgets import (
    QApplication,
    QAction,
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QProgressDialog,
    QPushButton,
    QSpinBox,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from core.system.mk4s_z_auto_approach import run_mk4s_z_move_to_setpoint
from core.ai.academic_ai_client import build_ai_recommendation
from core.ai.academic_gcode_generator import GCodePatternRequest, build_academic_gcode_job, build_gcode_plan
from core.ai.spm_approach_advisor import ApproachAdvisorInput, advise_approach
from core.z_control.crtouch_probe_plan import CRTouchProbePlan
from core.web.system_control import (
    system_apply_port,
    system_calibration,
    system_calibration_repeatability,
    system_diagnostics,
    system_disconnect,
    system_health_test,
    system_on,
    system_safe_standby,
    system_safe_standby_for_close,
)
from core.web.z_scanner_control import z_auto_approach, z_read_status, z_reference_payload, z_retract, z_stop_now
from core.web.spm_scan_simulation import WebScanProfile, build_scan_line
from core.web.real_scan_control import (
    clear_real_scan_pause,
    FoilTapConfig,
    request_real_scan_pause,
    request_real_scan_stop,
    run_real_foil_tap_scan,
    run_real_constant_z_scan,
)
from core.web.mk4s_motion_limits import motion_limits_payload


APP_VERSION = "v0.2.24"
APP_TITLE = f"SPM Prusa Operator Software {APP_VERSION} - Phase 2.1/2.4"
Z_VIEW_FULL_RANGE = (0.0, 220.0)
SYSTEM_CONTROL_WINDOW_WIDTH = 430
SYSTEM_CONTROL_WINDOW_HEIGHT = 760
GREEN_BUTTON_STYLE = "QPushButton { background: #167a3a; color: white; font-weight: 700; padding: 8px; }"
RED_BUTTON_STYLE = "QPushButton { background: #a71919; color: white; font-weight: 700; padding: 8px; }"
YELLOW_BUTTON_STYLE = "QPushButton { background: #c58a00; color: #101827; font-weight: 800; padding: 8px; }"
DISABLED_BUTTON_STYLE = "QPushButton { background: #4b5563; color: #d1d5db; font-weight: 700; padding: 8px; }"
GRAY_BUTTON_STYLE = "QPushButton { background: #d9dee7; color: #111827; font-weight: 700; padding: 8px; }"
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
        painter.fillRect(self.rect(), QColor("#050914"))
        painter.setRenderHint(QPainter.Antialiasing)

        width = self.width()
        height = self.height()
        margin_left = 48
        margin_right = 14
        margin_top = 26
        margin_bottom = 30
        plot_w = max(1, width - margin_left - margin_right)
        plot_h = max(1, height - margin_top - margin_bottom)

        painter.setPen(QPen(QColor("#263244"), 1))
        for i in range(6):
            y = margin_top + (plot_h * i / 5)
            painter.drawLine(margin_left, int(y), width - margin_right, int(y))

        painter.setPen(QColor("#9fb3c8"))
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

        painter.setPen(QPen(QColor("#5fd0ff"), 2))
        points = self.samples[-240:]
        last_x = last_y = None
        for index, value in enumerate(points):
            x = margin_left + int((index / max(1, len(points) - 1)) * plot_w)
            normalized = max(0.0, min(1.0, (value - low) / span))
            y = margin_top + plot_h - int(normalized * plot_h)
            if last_x is not None and last_y is not None:
                painter.drawLine(last_x, last_y, x, y)
            last_x, last_y = x, y

        painter.setPen(QColor("#d7e6f8"))
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
        painter.fillRect(self.rect(), QColor("#050914"))
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QColor("#d7e6f8"))
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
            painter.setPen(QColor("#9fb3c8"))
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

        painter.setPen(QPen(QColor("#263244"), 1))
        for i in range(5):
            y = top + int(height * i / 4)
            painter.drawLine(left, y, self.width() - right, y)

        painter.setPen(QPen(QColor("#5fd0ff"), 2))
        last_x = last_y = None
        point_pixels: list[tuple[int, int]] = []
        for index, value in enumerate(values):
            x = left + int(index / max(1, len(values) - 1) * width)
            y = top + height - int(((value - low) / span) * height)
            if last_x is not None:
                painter.drawLine(last_x, last_y, x, y)
            last_x, last_y = x, y
            point_pixels.append((x, y))

        painter.setPen(QPen(QColor("#b8efff"), 1))
        painter.setBrush(QColor("#5fd0ff"))
        for x, y in point_pixels:
            painter.drawEllipse(x - 3, y - 3, 6, 6)
        if point_pixels:
            x, y = point_pixels[-1]
            painter.setBrush(QColor("#ffffff"))
            painter.drawEllipse(x - 5, y - 5, 10, 10)

        painter.setPen(QColor("#d7e6f8"))
        latest_source = str(line[-1].get("feedback_source", "z_feedback"))
        painter.drawText(12, top + 4, f"{high:.3f} mm")
        painter.drawText(12, top + height, f"{low:.3f} mm")
        painter.drawText(left, self.height() - 10, f"{len(values)} points | latest {values[-1]:.4f} mm | {latest_source}")

    def paint_topography(self, painter: QPainter) -> None:
        rows = list(self.lines)
        if self.current_line:
            rows.append(list(self.current_line))
        if not rows:
            painter.setPen(QColor("#9fb3c8"))
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
                painter.setPen(QPen(QColor("#111827"), 1))
                painter.drawRect(cell_x, cell_y, cell_width, cell_height)

        painter.setPen(QColor("#d7e6f8"))
        painter.drawText(left, self.height() - 8, f"{len(rows)} lines | Z {low:.4f}..{high:.4f} mm")


class ToolWindow(QDialog):
    def closeEvent(self, event: Any) -> None:  # noqa: N802
        event.ignore()
        self.hide()


class ZScannerWindow(ToolWindow):
    def __init__(self, owner: "OperatorWorkstation") -> None:
        super().__init__(owner)
        self.setWindowTitle("Phase 2.2 Z Scanner")
        self.resize(980, 720)
        layout = QVBoxLayout()
        layout.addWidget(owner.build_z_panel())
        self.setLayout(layout)


class LiveLogWindow(ToolWindow):
    def __init__(self, owner: "OperatorWorkstation") -> None:
        super().__init__(owner)
        self.setWindowTitle("Phase 2.4 Live Log")
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
        self.setWindowTitle("Academic AI Print File Studio")
        self.resize(1220, 920)
        layout = QVBoxLayout()

        title = QLabel("Academic AI Print File Studio")
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
            label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
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

        workspace = QSplitter(Qt.Vertical)
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
        read_probe = QPushButton("Read Probe Status M119")
        read_probe.setStyleSheet(GREEN_BUTTON_STYLE)
        read_probe.clicked.connect(owner.read_z)
        actions.addWidget(read_probe)
        layout.addLayout(actions)
        self.setLayout(layout)


class MeasurementWindow(ToolWindow):
    def __init__(self, owner: "OperatorWorkstation") -> None:
        super().__init__(owner)
        self.owner = owner
        self.setWindowTitle("Phase 2.3 Measurement Control")
        self.resize(980, 760)

        layout = QVBoxLayout()
        self.x_size = QDoubleSpinBox()
        self.y_size = QDoubleSpinBox()
        self.x_points = QSpinBox()
        self.y_lines = QSpinBox()
        self.scan_speed = QDoubleSpinBox()
        self.scan_direction = QComboBox()
        self.surface = QComboBox()
        self.resolution_status = QLabel()

        self.x_size.setRange(0.1, 200.0)
        self.y_size.setRange(0.1, 200.0)
        self.x_size.setValue(100.0)
        self.y_size.setValue(100.0)
        self.x_points.setRange(2, 500)
        self.y_lines.setRange(1, 500)
        self.x_points.setValue(10)
        self.y_lines.setValue(10)
        self.scan_speed.setRange(0.1, 50.0)
        self.scan_speed.setDecimals(2)
        self.scan_speed.setValue(5.0)
        self.scan_direction.addItems(["X+", "X-", "Y+", "Y-"])
        self.surface.addItems(["sphere_on_plane", "terrace", "grid_atoms", "bravais_lattice"])
        for widget in (self.x_size, self.y_size):
            widget.valueChanged.connect(self.update_resolution_status)
        self.x_points.valueChanged.connect(self.update_resolution_status)
        self.y_lines.valueChanged.connect(self.update_resolution_status)
        self.scan_speed.valueChanged.connect(self.update_resolution_status)
        self.scan_direction.currentTextChanged.connect(lambda _text: self.update_resolution_status())

        xy_group = QGroupBox("Phase 2.3 XY Raster")
        xy_form = QFormLayout()
        xy_form.addRow("X range mm", self.x_size)
        xy_form.addRow("Y range mm", self.y_size)
        xy_form.addRow("X points", self.x_points)
        xy_form.addRow("Y lines", self.y_lines)
        xy_form.addRow("Scan direction", self.scan_direction)
        xy_form.addRow("Scan speed mm/s", self.scan_speed)
        xy_form.addRow("Simulation surface", self.surface)
        xy_group.setLayout(xy_form)

        layout.addWidget(xy_group)
        self.resolution_status.setWordWrap(True)
        self.resolution_status.setStyleSheet("border: 1px solid #8da2b8; padding: 8px; background: #f8fbff;")
        layout.addWidget(self.resolution_status)

        actions = QHBoxLayout()
        real_start = QPushButton("Start Constant-Z Raster")
        foil_tap = QPushButton("Start Tapping Scan 50x50")
        start = QPushButton("Start Simulation")
        pause = QPushButton("Pause")
        stop = QPushButton("Stop")
        for button in (real_start, foil_tap, start):
            button.setStyleSheet(GREEN_BUTTON_STYLE)
        stop.setStyleSheet(RED_BUTTON_STYLE)
        real_start.clicked.connect(self.start_real_scan)
        foil_tap.clicked.connect(self.start_foil_tap_scan)
        start.clicked.connect(self.start_measurement)
        pause.clicked.connect(owner.pause_measurement)
        stop.clicked.connect(owner.stop_measurement)
        actions.addWidget(real_start)
        actions.addWidget(foil_tap)
        actions.addWidget(start)
        actions.addWidget(pause)
        actions.addWidget(stop)
        layout.addLayout(actions)

        view_actions = QHBoxLayout()
        open_line = QPushButton("Open Line Window")
        open_topography = QPushButton("Open Topography Window")
        open_line.clicked.connect(lambda: owner.open_signal_window("line", "X+"))
        open_topography.clicked.connect(lambda: owner.open_signal_window("topography", "X+"))
        view_actions.addWidget(open_line)
        view_actions.addWidget(open_topography)
        layout.addLayout(view_actions)

        self.status = QLabel(
            "Measurement Control owns XY raster and signal views. Z setpoint, auto approach, tapping limits, "
            "retract, and emergency stop are controlled in Tools -> Z Scanner. Table/plate reference is Z=0."
        )
        self.status.setWordWrap(True)
        self.status.setStyleSheet("border: 1px solid #8da2b8; padding: 8px; background: #f8fbff;")
        layout.addWidget(self.status)

        preview_grid = QGridLayout()
        self.line_preview = SignalPlotWidget("Measurement Progress - Line Mode X+", "line", "X+")
        self.topography_preview = SignalPlotWidget("Measurement Progress - Topography X+", "topography", "X+")
        self.line_preview.setMinimumSize(420, 230)
        self.topography_preview.setMinimumSize(420, 230)
        preview_grid.addWidget(self.line_preview, 0, 0)
        preview_grid.addWidget(self.topography_preview, 0, 1)
        layout.addLayout(preview_grid)
        self.setLayout(layout)
        self.update_resolution_status()

    def profile(self) -> WebScanProfile:
        cx, cy = 125.0, 105.0
        half_x = self.x_size.value() / 2.0
        half_y = self.y_size.value() / 2.0
        return WebScanProfile(
            x_min=cx - half_x,
            x_max=cx + half_x,
            y_min=cy - half_y,
            y_max=cy + half_y,
            x_points=int(self.x_points.value()),
            y_points=int(self.y_lines.value()),
            z_setpoint=float(self.owner.target_z.value()),
            feedback_gain=float(self.owner.feedback_gain.value()),
            surface=str(self.surface.currentText()),
            serpentine=True,
            scan_direction=str(self.scan_direction.currentText()),
        )

    def foil_tap_config(self) -> FoilTapConfig:
        return FoilTapConfig(
            z_setpoint_mm=float(self.owner.target_z.value()),
            tapping_range_mm=float(self.owner.tapping_range.value()),
            approach_speed_mm_s=float(self.owner.approach_speed.value()),
            retract_after_tap_mm=float(self.owner.tap_retract_z.value()),
            full_retract_z_mm=float(self.owner.full_retract_z.value()),
        )

    def update_resolution_status(self) -> None:
        limits = motion_limits_payload()
        xy_resolution_um = float(limits["xy_command_resolution_um"])
        x_step = self.x_size.value() / max(1, self.x_points.value() - 1)
        y_step = self.y_size.value() / max(1, self.y_lines.value() - 1)
        direction = str(self.scan_direction.currentText())
        primary_step = x_step if direction.startswith("X") else y_step
        secondary_step = y_step if direction.startswith("X") else x_step
        self.resolution_status.setText(
            f"Direction {direction}: primary step {primary_step:.3f} mm, line step {secondary_step:.3f} mm. "
            f"MK4S command resolution is about {xy_resolution_um:.1f} um; scan quality is set by step size, "
            f"speed {self.scan_speed.value():.2f} mm/s, mechanics, and validated contact feedback."
        )

    def start_measurement(self) -> None:
        if self.owner.start_measurement_simulation(self.profile(), self.scan_speed.value()):
            self.status.setText("Measurement simulation running. Line/topography windows update point by point.")

    def start_real_scan(self) -> None:
        if self.owner.start_measurement_real_scan(self.profile(), self.scan_speed.value()):
            self.status.setText("Constant-Z raster requested. This mode reads M114 at each XY point but does not tap.")

    def start_foil_tap_scan(self) -> None:
        self.x_size.setValue(50.0)
        self.y_size.setValue(50.0)
        self.x_points.setValue(10)
        self.y_lines.setValue(10)
        if self.owner.start_measurement_foil_tap_scan(self.profile(), self.foil_tap_config(), self.scan_speed.value()):
            self.status.setText("Tapping scan requested. Each point approaches, records contact Z, retracts, then steps XY.")

    def update_progress_views(self, lines: list[list[dict[str, float]]], current_line: list[dict[str, float]]) -> None:
        self.line_preview.set_scan_data(lines, current_line)
        self.topography_preview.set_scan_data(lines, current_line)


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


class OperatorWorkstation(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.setFixedSize(SYSTEM_CONTROL_WINDOW_WIDTH, SYSTEM_CONTROL_WINDOW_HEIGHT)
        self.worker: QThread | None = None
        self.last_system_payload: dict[str, Any] = {}
        self.latest_z_value = 120.0
        self.z_scanner_window: ZScannerWindow | None = None
        self.live_log_window: LiveLogWindow | None = None
        self.academic_gcode_window: AcademicGCodeWindow | None = None
        self.crtouch_prep_window: CRTouchPrepWindow | None = None
        self.measurement_window: MeasurementWindow | None = None
        self.signal_windows: dict[str, QDialog] = {}
        self.signal_plots: dict[str, SignalPlotWidget] = {}
        self.measurement_timer = QTimer(self)
        self.measurement_timer.timeout.connect(self.advance_measurement_point)
        self.measurement_profile: WebScanProfile | None = None
        self.measurement_lines: list[list[dict[str, float]]] = []
        self.measurement_current_line: list[dict[str, float]] = []
        self.measurement_line_payload: dict[str, Any] | None = None
        self.measurement_line_index = 0
        self.measurement_point_index = 0
        self.measurement_paused = False
        self._safe_close_in_progress = False
        self.system_connected = False
        self.system_busy = False

        root = QWidget()
        layout = QGridLayout()
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        layout.addWidget(self.build_system_panel(), 0, 0)
        root.setLayout(layout)
        self.setCentralWidget(root)

        self.z_scanner_window = ZScannerWindow(self)
        self.live_log_window = LiveLogWindow(self)
        self.academic_gcode_window = AcademicGCodeWindow(self)
        self.crtouch_prep_window = CRTouchPrepWindow(self)
        self.measurement_window = MeasurementWindow(self)
        self.build_menu_bar()

        self.append_log(f"{APP_TITLE} loaded. Web UI snapshot is preserved separately.")
        self.load_z_reference()

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
        for label in LINE_VIEW_LABELS:
            direction = label.rsplit(" ", 1)[-1]
            view_menu.addAction(label, lambda _checked=False, d=direction: self.open_signal_window("line", d))
        view_menu.addSeparator()
        for label in TOPOGRAPHY_VIEW_LABELS:
            direction = label.rsplit(" ", 1)[-1]
            view_menu.addAction(label, lambda _checked=False, d=direction: self.open_signal_window("topography", d))

        tools_menu = menu.addMenu("Tools")
        tools_menu.addAction("Z Scanner", self.open_z_scanner_window)
        tools_menu.addAction("Measurement Control", self.open_measurement_window)
        tools_menu.addAction("Live Log", self.open_live_log_window)
        tools_menu.addAction("Academic AI Print File Export", self.open_academic_gcode_window)
        tools_menu.addAction("CR Touch Probe Prep", self.open_crtouch_prep_window)
        tools_menu.addSeparator()
        tools_menu.addAction("Connect Read-Only", self.connect_system)
        tools_menu.addAction("Run Diagnosis", self.run_diagnosis)
        tools_menu.addAction("Safe Standby", self.safe_standby)
        tools_menu.addAction("AI Error Correction", self.ai_error_correction)
        tools_menu.addSeparator()
        tools_menu.addAction("Read Z", self.read_z)
        tools_menu.addAction("Stop Z", self.stop_z)

        about_menu = menu.addMenu("About")
        about_menu.addAction("About SPM Operator Software", self.show_about)

    def request_safe_exit(self) -> None:
        self.append_system_message("Close requested. Running Safe Standby before exit.")
        self.close()

    def closeEvent(self, event: Any) -> None:  # noqa: N802
        if self._safe_close_in_progress:
            event.accept()
            return

        event.ignore()
        if not self.safe_shutdown_before_close():
            return

        self._safe_close_in_progress = True
        self.close()

    def safe_shutdown_before_close(self) -> bool:
        if self.worker and self.worker.isRunning():
            request_real_scan_stop()
            z_stop_now()

        progress = QProgressDialog(
            "Parking hardware at safe standby position...\n\nTarget: X125 Y105 Z120\nThen disconnecting.",
            "",
            0,
            0,
            self,
        )
        progress.setWindowTitle("Safe Shutdown")
        progress.setCancelButton(None)
        progress.setWindowModality(Qt.ApplicationModal)
        progress.setMinimumDuration(0)
        progress.show()
        QApplication.processEvents()

        try:
            self.append_log("[SAFE CLOSE] Close requested. Parking to X125 Y105 Z120 before exit.")
            self.append_system_message("Safe close: stopping active work, then parking X125 Y105 Z120.")
            if self.worker and self.worker.isRunning():
                self.append_log("[SAFE CLOSE] Active hardware worker detected. Stop requested; waiting before park.")
                self.append_system_message("Safe close: waiting for active hardware command to stop.")
                if not self.worker.wait(15000):
                    self.append_system_message("Safe close blocked: active command did not stop within 15 seconds.")
                    QMessageBox.warning(
                        self,
                        "Safe Shutdown Waiting",
                        "The active hardware command did not stop within 15 seconds.\n\n"
                        "The software will stay open so you can press STOP Z or recover manually.",
                    )
                    return False

            self.append_system_message("Safe close: sending default standby target X125 Y105 Z120.")
            QApplication.processEvents()
            standby = system_safe_standby_for_close()
            self.render_system_payload(standby)
            self.render_payload_log(standby)
            if not standby.get("ok"):
                self.append_system_message(f"Safe close blocked: {standby.get('message', 'standby failed')}")
                QMessageBox.warning(
                    self,
                    "Safe Shutdown Blocked",
                    "The software did not close because Safe Standby failed.\n\n"
                    f"{standby.get('message', 'Unknown standby error')}",
                )
                return False

            self.append_system_message("Safe close: standby verified. Disconnecting.")
            QApplication.processEvents()
            disconnect = system_disconnect()
            self.render_system_payload(disconnect)
            self.render_payload_log(disconnect)
            if not disconnect.get("ok"):
                self.append_system_message(f"Safe close blocked: {disconnect.get('message', 'disconnect failed')}")
                QMessageBox.warning(
                    self,
                    "Safe Shutdown Blocked",
                    "The software did not close because disconnect failed.\n\n"
                    f"{disconnect.get('message', 'Unknown disconnect error')}",
                )
                return False

            self.append_log("[SAFE CLOSE] Hardware parked, disconnected, and software close is allowed.")
            self.append_system_message("Safe close complete. Hardware parked, disconnected, close allowed.")
            return True
        finally:
            progress.close()

    def build_system_panel(self) -> QGroupBox:
        box = QGroupBox("Phase 2.1 System Control")
        layout = QVBoxLayout()
        layout.setContentsMargins(12, 16, 12, 12)
        layout.setSpacing(9)

        self.port_select = QComboBox()
        self.port_select.addItems(["AUTO", "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9", "COM10"])
        self.port_select.setCurrentText("COM6")
        self.port_select.setMinimumHeight(34)

        self.system_state = QLabel("System: not connected")
        self.system_state.setWordWrap(True)
        self.system_state.setMinimumHeight(170)
        self.system_state.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.system_state.setStyleSheet("border: 1px solid #8da2b8; padding: 10px; background: #f8fbff;")

        self.connect_button = QPushButton("Connect")
        self.disconnect_button = QPushButton("Disconnect")
        diagnosis = QPushButton("Diagnosis")
        calibration = QPushButton("Calibrate MK4S")
        ai_fix = QPushButton("AI Error Correction")
        standby = QPushButton("Safe Standby X125 Y105 Z120")
        close_button = QPushButton("Close Safely")
        for button in (self.connect_button, self.disconnect_button, diagnosis, calibration, ai_fix, standby, close_button):
            button.setMinimumHeight(38)
        self.connect_button.setStyleSheet(YELLOW_BUTTON_STYLE)
        diagnosis.setStyleSheet(GRAY_BUTTON_STYLE)
        calibration.setStyleSheet(GRAY_BUTTON_STYLE)
        ai_fix.setStyleSheet(GRAY_BUTTON_STYLE)
        standby.setStyleSheet(GRAY_BUTTON_STYLE)
        close_button.setStyleSheet(GRAY_BUTTON_STYLE)
        self.disconnect_button.setStyleSheet(RED_BUTTON_STYLE)
        self.disconnect_button.setEnabled(False)
        self.connect_button.clicked.connect(self.connect_system)
        self.disconnect_button.clicked.connect(self.disconnect_system)
        diagnosis.clicked.connect(self.run_diagnosis)
        calibration.clicked.connect(self.run_calibration)
        ai_fix.clicked.connect(self.ai_error_correction)
        standby.clicked.connect(self.safe_standby)
        close_button.clicked.connect(self.request_safe_exit)

        self.system_log = QTextEdit()
        self.system_log.setReadOnly(True)
        self.system_log.setMaximumHeight(120)
        self.system_log.setStyleSheet("font-family: Consolas, monospace; background: #f8fbff; border: 1px solid #8da2b8;")
        self.system_log.setPlainText("Phase 2.1 ready. Connect to begin.")

        layout.addWidget(QLabel("Port"))
        layout.addWidget(self.port_select)
        layout.addWidget(self.connect_button)
        layout.addWidget(self.disconnect_button)
        layout.addWidget(diagnosis)
        layout.addWidget(calibration)
        layout.addWidget(ai_fix)
        layout.addWidget(standby)
        layout.addWidget(close_button)
        layout.addWidget(self.system_state, 1)
        layout.addWidget(QLabel("Phase 2.1 communication"))
        layout.addWidget(self.system_log)
        box.setLayout(layout)
        box.setMinimumSize(400, 555)
        return box

    def build_z_panel(self) -> QGroupBox:
        box = QGroupBox("Phase 2.2 Z Scanner")
        layout = QVBoxLayout()

        readouts = QHBoxLayout()
        self.current_z = QLabel("Current Z: --")
        self.count_z = QLabel("Count Z: --")
        self.clearance = QLabel("Clearance: --")
        for label in (self.current_z, self.count_z, self.clearance):
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
        scale_row.addWidget(QLabel("Z display"))
        scale_row.addWidget(full)
        scale_row.addWidget(auto)
        scale_row.addWidget(zoom)
        scale_row.addWidget(QLabel("Zoom window mm"))
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
        self.tap_retract_z = QDoubleSpinBox()
        self.tap_retract_z.setRange(0.1, 30.0)
        self.tap_retract_z.setDecimals(3)
        self.tap_retract_z.setValue(3.0)
        self.full_retract_z = QDoubleSpinBox()
        self.full_retract_z.setRange(0.1, 221.0)
        self.full_retract_z.setDecimals(3)
        self.full_retract_z.setValue(120.0)
        form.addRow("Z setpoint / contact limit mm", self.target_z)
        form.addRow("Tapping range above setpoint mm", self.tapping_range)
        form.addRow("Expected surface Z mm", self.expected_surface_z)
        form.addRow("Approach speed mm/s", self.approach_speed)
        form.addRow("Table reference Z mm", QLabel("0.000 - scanner plate / XY table"))
        form.addRow("Full retract Z mm", self.full_retract_z)
        layout.addLayout(form)

        actions = QHBoxLayout()
        read = QPushButton("Read Z")
        advisor = QPushButton("Approach Advisor")
        apply = QPushButton("Manual Approach to Setpoint")
        auto_approach = QPushButton("Auto Approach")
        retract = QPushButton("Retract Z")
        stop = QPushButton("STOP Z")
        advisor.setStyleSheet(GRAY_BUTTON_STYLE)
        for button in (apply, auto_approach):
            button.setStyleSheet(GREEN_BUTTON_STYLE)
        for button in (retract, stop):
            button.setStyleSheet(RED_BUTTON_STYLE)
        read.clicked.connect(self.read_z)
        advisor.clicked.connect(self.run_approach_advisor)
        apply.clicked.connect(self.apply_target_z)
        auto_approach.clicked.connect(self.auto_approach_z)
        retract.clicked.connect(self.retract_z)
        stop.clicked.connect(self.stop_z)
        actions.addWidget(read)
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

    def update_system_connection_controls(self, *, connected: bool | None = None, busy: bool | None = None) -> None:
        if connected is not None:
            self.system_connected = bool(connected)
        if busy is not None:
            self.system_busy = bool(busy)
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
            self.connect_button.setEnabled(True)
            self.disconnect_button.setEnabled(True)
            self.disconnect_button.setStyleSheet(RED_BUTTON_STYLE)
            return

        self.connect_button.setText("Connect")
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
            self.append_system_message("Already connected. You can run Diagnosis, open Z Scanner, or start Measurement Control.")
            return
        port = self.selected_port()

        def action() -> dict[str, Any]:
            system_apply_port(port)
            return system_on(mode="hardware_readonly", port=port)

        self.update_system_connection_controls(connected=False, busy=True)
        self.system_state.setText("Connecting to MK4S read-only hardware interface...")
        self.append_system_message("Connecting to MK4S read-only hardware interface.")
        if not self.run_worker(action, self.render_system_payload):
            self.update_system_connection_controls(busy=False)

    def disconnect_system(self) -> None:
        self.update_system_connection_controls(busy=True)
        self.system_state.setText("Disconnecting safely...")
        self.append_system_message("Disconnect requested. Safe retract/standby state will be checked before disconnect.")
        if not self.run_worker(system_disconnect, self.render_system_payload):
            self.update_system_connection_controls(busy=False)

    def run_calibration(self) -> None:
        if QMessageBox.question(self,"MK4S Calibration","Home all axes (G28) and verify endstops?\n\nPrinter will move. Clear the scan area.") != QMessageBox.Yes:
            return
        self.append_system_message("Calibration started. Homing all axes via G28...")
        self.run_worker(lambda: system_calibration(port=self.selected_port() or None),self.render_system_payload)

    def run_diagnosis(self) -> None:
        if QMessageBox.question(
            self,
            "Diagnosis",
            "Run Phase 2.1 diagnosis? This checks position and may run the visible XYZ health movement if enabled.",
        ) != QMessageBox.Yes:
            return
        self.append_system_message("Diagnosis started. The printer may run visible health movement if enabled.")

        def action() -> dict[str, Any]:
            diagnostic = system_diagnostics()
            if not diagnostic.get("ok"):
                return diagnostic
            health = system_health_test(confirmed="1", motion="1", profile="short")
            return {
                **health,
                "log_lines": list(diagnostic.get("log_lines") or []) + list(health.get("log_lines") or []),
            }

        self.run_worker(action, self.render_system_payload)

    def ai_error_correction(self) -> None:
        context = {
            "system": self.last_system_payload,
            "z_state": self.z_state.text(),
            "latest_z": self.current_z.text(),
        }
        payload = build_ai_recommendation(task="diagnosis / error correction", context=context)
        lines = [
            "AI ERROR CORRECTION ADVISORY:",
            *(str(item) for item in payload.get("recommendation", [])),
            f"Safety: {payload.get('safety_note', 'advisory only')}",
        ]
        QMessageBox.information(self, "AI Error Correction", "\n".join(lines))
        for line in lines:
            self.append_log(line)

    def safe_standby(self) -> None:
        if QMessageBox.question(self, "Safe Standby", "Move to X125 Y105 Z120?") != QMessageBox.Yes:
            return
        self.append_system_message("Safe Standby requested: X125 Y105 Z120.")
        self.run_worker(system_safe_standby, self.render_system_payload)

    def load_z_reference(self) -> None:
        payload = z_reference_payload()
        self.z_state.setText(
            f"Z reference: surface {payload['surface_z_mm']:.3f} mm, safe minimum {payload['safe_min_z_mm']:.3f} mm"
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
        if QMessageBox.question(
            self,
            "Manual Approach to Setpoint",
            f"Move Z directly to setpoint {target:.3f} mm without feedback?",
        ) != QMessageBox.Yes:
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
        if QMessageBox.question(
            self,
            "Auto Approach Simulation",
            (
                f"Simulate feedback approach through {tapping_range:.3f} mm down to "
                f"Z setpoint {setpoint:.3f} mm at {approach_speed:.3f} mm/s?\n\n"
                "Real sensor-based approach is disabled until the feedback sensor is verified."
            ),
        ) != QMessageBox.Yes:
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
        if QMessageBox.question(self, "Retract Z", "Retract Z to the configured safe height?") != QMessageBox.Yes:
            return
        self.run_worker(lambda: z_retract(confirmed=True), self.render_z_payload)

    def stop_z(self) -> None:
        request_real_scan_stop()
        payload = z_stop_now()
        self.render_z_payload(payload)
        self.render_payload_log(payload)

    def render_system_payload(self, payload: dict[str, Any]) -> None:
        self.last_system_payload = dict(payload)
        connected = bool(
            payload.get("ok")
            and payload.get("mode") == "real_hardware_readonly"
            and (
                payload.get("connected")
                or payload.get("powered")
                or payload.get("ready")
            )
            and payload.get("status") != "disconnected"
        )
        self.update_system_connection_controls(connected=connected, busy=False)
        position = payload.get("position") or (payload.get("hardware") or {}).get("position") or ""
        self.system_state.setText(
            f"ok={payload.get('ok')} status={payload.get('status')} mode={payload.get('mode')}\n"
            f"port={payload.get('port', '')}\n{position}\n{payload.get('message', '')}"
        )
        message = str(payload.get("message", "") or payload.get("status", ""))
        if connected:
            self.append_system_message(f"Connected on {payload.get('port', '') or 'selected port'}. You can run Diagnosis, open Z Scanner, or open Measurement Control.")
        elif payload.get("status") == "disconnected":
            self.append_system_message("Disconnected. It is safe to connect again or close the software.")
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
        self.z_state.setText(f"ok={payload.get('ok')} status={payload.get('status')}\n{payload.get('message', '')}")

    def render_payload_log(self, payload: dict[str, Any]) -> None:
        for line in payload.get("log_lines") or [payload.get("message", "")]:
            self.append_log(str(line))

    def append_log(self, message: str) -> None:
        if message:
            self.log.append(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")

    def append_system_message(self, message: str) -> None:
        if message and hasattr(self, "system_log"):
            self.system_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")

    def clear_log(self) -> None:
        self.log.clear()
        self.append_log("Live log cleared.")

    def download_log(self) -> None:
        default = PROJECT_ROOT / "logs" / f"spm_operator_software_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        default.parent.mkdir(parents=True, exist_ok=True)
        path, _ = QFileDialog.getSaveFileName(self, "Download Live Log", str(default), "Text files (*.txt);;All files (*)")
        if not path:
            return
        Path(path).write_text(self.log.toPlainText(), encoding="utf-8")
        self.append_log(f"Live log saved: {path}")

    def show_about(self) -> None:
        QMessageBox.information(
            self,
            "About",
            f"{APP_TITLE}\n\nDesktop migration path for the SPM Prusa scanner.\n"
            "Motion remains gated by local safety checks and environment flags.",
        )

    def open_z_scanner_window(self) -> None:
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
        if self.academic_gcode_window is not None:
            self.academic_gcode_window.show()
            self.academic_gcode_window.raise_()
            self.academic_gcode_window.activateWindow()

    def open_crtouch_prep_window(self) -> None:
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

    def start_measurement_simulation(self, profile: WebScanProfile, scan_speed_mm_s: float) -> bool:
        try:
            profile.validate()
        except ValueError as exc:
            QMessageBox.warning(self, "Measurement profile invalid", str(exc))
            return False
        self.measurement_timer.stop()
        self.measurement_profile = profile
        self.measurement_lines = []
        self.measurement_current_line = []
        self.measurement_line_payload = build_scan_line(profile, 0)
        self.measurement_line_index = 0
        self.measurement_point_index = 0
        self.measurement_paused = False
        interval_ms = max(1, int(1000.0 / max(1.0, scan_speed_mm_s * 20.0)))
        self.measurement_timer.start(interval_ms)
        self.append_log(
            f"[MEASUREMENT] Simulated scan started: {profile.x_points} points x {profile.y_points} lines, "
            f"speed {scan_speed_mm_s:.2f} mm/s"
        )
        self.refresh_signal_windows()
        return True

    def pause_measurement(self) -> None:
        self.measurement_paused = not self.measurement_paused
        if self.measurement_paused:
            request_real_scan_pause()
        else:
            clear_real_scan_pause()
        self.append_log(f"[MEASUREMENT] {'Paused' if self.measurement_paused else 'Resumed'}")

    def stop_measurement(self) -> None:
        self.measurement_timer.stop()
        self.measurement_paused = False
        clear_real_scan_pause()
        request_real_scan_stop()
        self.append_log("[MEASUREMENT] Stopped")

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
        ) != QMessageBox.Yes:
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
        ) != QMessageBox.Yes:
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

    def advance_measurement_point(self) -> None:
        if self.measurement_paused or self.measurement_profile is None or self.measurement_line_payload is None:
            return
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
                return
            self.measurement_line_payload = build_scan_line(self.measurement_profile, self.measurement_line_index)
            self.measurement_point_index = 0
            points = self.measurement_line_payload["points"]

        point = dict(points[self.measurement_point_index])
        self.measurement_point_index += 1
        self.measurement_current_line.append(point)
        z_value = float(point["z_feedback"])
        self.latest_z_value = z_value
        self.z_trace.add_sample(z_value)
        self.current_z.setText(f"Current Z: {z_value:.3f} mm")
        self.z_state.setText(
            f"Measurement simulation: line {self.measurement_line_index + 1}/{self.measurement_profile.y_points}, "
            f"point {self.measurement_point_index}/{self.measurement_profile.x_points}, Z={z_value:.4f} mm"
        )
        self.refresh_signal_windows()

    def refresh_signal_windows(self) -> None:
        if self.measurement_window is not None:
            self.measurement_window.update_progress_views(self.measurement_lines, self.measurement_current_line)
        for plot in self.signal_plots.values():
            plot.set_scan_data(self.measurement_lines, self.measurement_current_line)


def main() -> int:
    app = QApplication(sys.argv)
    window = OperatorWorkstation()
    window.show()
    return app.exec_()


if __name__ == "__main__":
    raise SystemExit(main())
