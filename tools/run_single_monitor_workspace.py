from __future__ import annotations

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

os.chdir(PROJECT_ROOT)

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QDoubleSpinBox,
    QGroupBox,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QWidget,
)

from core.application.operator_workstation_software import OperatorWorkstation


def compact_tree(root: QWidget) -> None:
    """Compact presentation only. No hardware behavior is modified."""

    normal = QFont()
    normal.setPointSize(9)

    small = QFont()
    small.setPointSize(8)

    for widget in root.findChildren(QPushButton):
        widget.setFont(normal)
        widget.setMinimumHeight(24)
        widget.setMaximumHeight(28)

    for widget in root.findChildren(QComboBox):
        widget.setFont(normal)
        widget.setMinimumHeight(24)
        widget.setMaximumHeight(27)

    for widget in root.findChildren((QSpinBox, QDoubleSpinBox)):
        widget.setFont(normal)
        widget.setMinimumHeight(24)
        widget.setMaximumHeight(27)

    for widget in root.findChildren(QLineEdit):
        widget.setFont(normal)
        widget.setMinimumHeight(23)
        widget.setMaximumHeight(27)

    for widget in root.findChildren(QLabel):
        widget.setFont(normal)

    for widget in root.findChildren(QGroupBox):
        widget.setFont(normal)

    for widget in root.findChildren((QTextEdit, QPlainTextEdit)):
        widget.setFont(small)


def hide_main_window_duplicates(window: OperatorWorkstation) -> None:
    """
    Main window becomes the dedicated control rail.
    Overview/log duplicates are hidden because the measurement and
    live-data windows remain visible beside it.
    """

    for group in window.findChildren(QGroupBox):
        if group.title() in {"System Overview", "Logs"}:
            group.hide()

    # Remove large header controls from the narrow control rail.
    for name in (
        "repeat_two_object_button",
        "two_object_resolution",
        "mount_profile_label",
        "profile_select",
    ):
        widget = getattr(window, name, None)
        if widget is not None:
            widget.hide()

    for button in window.findChildren(QPushButton):
        if "Project Handbook" in button.text():
            button.hide()

    for label in window.findChildren(QLabel):
        if label.text().strip() == "Profile:":
            label.hide()


def main() -> int:
    app = QApplication(sys.argv)

    app_font = app.font()
    app_font.setPointSize(9)
    app.setFont(app_font)

    control = OperatorWorkstation()

    # Explicit safety state for this workspace.
    control.apply_motion_authorization("LOCKED", confirm=False)

    scan = control.z_scanner_window
    live = control.live_log_window

    if scan is None or live is None:
        raise RuntimeError("Required SPM workspace windows were not created.")

    hide_main_window_duplicates(control)

    compact_tree(control)
    compact_tree(scan)
    compact_tree(live)

    screen = app.primaryScreen()
    if screen is None:
        raise RuntimeError("No graphical display detected.")

    area = screen.availableGeometry()

    x = area.x()
    y = area.y()
    width = area.width()
    height = area.height()

    gap = 6

    # One-monitor scientific workstation proportions:
    # 20% controls / 56% measurement / 24% live data.
    control_w = int(width * 0.20)
    live_w = int(width * 0.24)
    measure_w = width - control_w - live_w - (2 * gap)

    # Allow the control rail to become narrow despite the old desktop layout.
    control.setMinimumSize(320, 600)
    control.setWindowTitle("SPM — CONTROL")

    scan.setMinimumSize(640, 600)
    scan.setWindowTitle("SPM — MEASUREMENT / SCAN")

    live.setMinimumSize(360, 400)
    live.setWindowTitle("SPM — LIVE DATA")

    for win in (control, scan, live):
        win.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.WindowMinMaxButtonsHint
            | Qt.WindowType.WindowCloseButtonHint
        )

    control.setGeometry(
        x,
        y,
        control_w,
        height,
    )

    scan.setGeometry(
        x + control_w + gap,
        y,
        measure_w,
        height,
    )

    live.setGeometry(
        x + control_w + gap + measure_w + gap,
        y,
        live_w,
        height,
    )

    control.show()
    scan.show()
    live.show()

    control.raise_()
    scan.raise_()
    live.raise_()

    print("SINGLE_MONITOR_WORKSPACE=ACTIVE")
    print(
        f"CONTROL={control_w}px "
        f"MEASUREMENT={measure_w}px "
        f"LIVE={live_w}px"
    )
    print("MOTION_AUTHORIZATION=LOCKED")
    print("USB_HARDWARE_REQUIRED=NO")

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
