from __future__ import annotations

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
os.chdir(PROJECT_ROOT)

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QDoubleSpinBox,
    QTextEdit,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)

from core.application.operator_workstation_software import OperatorWorkstation


def find_system_group(control: OperatorWorkstation) -> QGroupBox:
    """
    Locate the existing live System Control group using the Connect button.
    We re-use the original widgets and callbacks; no hardware logic is copied.
    """
    widget = control.connect_button

    parent = widget.parentWidget()
    while parent is not None:
        if isinstance(parent, QGroupBox):
            return parent
        parent = parent.parentWidget()

    raise RuntimeError("Could not locate System Control group.")


def compact_controls(root: QWidget) -> None:
    font = QFont()
    font.setPointSize(8)

    for w in root.findChildren(QLabel):
        w.setFont(font)

    for w in root.findChildren(QPushButton):
        w.setFont(font)
        w.setMinimumHeight(22)
        w.setMaximumHeight(25)
        w.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )

    for w in root.findChildren(QComboBox):
        w.setFont(font)
        w.setMinimumHeight(22)
        w.setMaximumHeight(25)

    for w in root.findChildren((QSpinBox, QDoubleSpinBox)):
        w.setFont(font)
        w.setMinimumHeight(22)
        w.setMaximumHeight(25)

    for w in root.findChildren(QLineEdit):
        w.setFont(font)
        w.setMinimumHeight(21)
        w.setMaximumHeight(24)

    for w in root.findChildren((QTextEdit, QPlainTextEdit)):
        w.setFont(font)

    for group in root.findChildren(QGroupBox):
        group.setFont(font)


class CompactControlWindow(QMainWindow):
    def __init__(self, control: OperatorWorkstation):
        super().__init__()

        self.control = control

        self.setWindowTitle("SPM CONTROL")
        self.setMinimumWidth(350)
        self.resize(390, 920)

        self.setStyleSheet("""
            QMainWindow {
                background: #111827;
            }

            QWidget {
                font-size: 8pt;
            }

            QFrame#header {
                background: #172033;
                border: 1px solid #334155;
                border-radius: 5px;
            }

            QLabel#title {
                color: #f8fafc;
                font-size: 12pt;
                font-weight: 700;
            }

            QLabel#subtitle {
                color: #94a3b8;
                font-size: 8pt;
            }

            QLabel#connectionBadge {
                padding: 3px 7px;
                border-radius: 4px;
                font-weight: 700;
            }

            QLabel#authBadge {
                padding: 3px 7px;
                border-radius: 4px;
                font-weight: 700;
            }

            QGroupBox {
                border: 1px solid #475569;
                border-radius: 5px;
                margin-top: 9px;
                padding-top: 5px;
                font-weight: 700;
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0px 3px;
            }

            QPushButton {
                min-height: 22px;
                max-height: 25px;
                padding: 1px 6px;
                border-radius: 3px;
            }

            QComboBox, QSpinBox, QDoubleSpinBox, QLineEdit {
                min-height: 21px;
                max-height: 24px;
            }

            QScrollArea {
                border: none;
                background: transparent;
            }
        """)

        central = QWidget()
        outer = QVBoxLayout(central)
        outer.setContentsMargins(6, 6, 6, 6)
        outer.setSpacing(5)

        # --------------------------------------------------
        # COMPACT HEADER
        # --------------------------------------------------

        header = QFrame()
        header.setObjectName("header")

        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(8, 6, 8, 6)
        header_layout.setSpacing(3)

        top = QHBoxLayout()

        title_box = QVBoxLayout()

        title = QLabel("SPM CONTROL")
        title.setObjectName("title")

        subtitle = QLabel("MK4S · CR-Touch · Safety")
        subtitle.setObjectName("subtitle")

        title_box.addWidget(title)
        title_box.addWidget(subtitle)

        top.addLayout(title_box)
        top.addStretch(1)

        self.connection_badge = QLabel("OFFLINE")
        self.connection_badge.setObjectName("connectionBadge")

        self.authorization_badge = QLabel("LOCKED")
        self.authorization_badge.setObjectName("authBadge")

        top.addWidget(self.connection_badge)
        top.addWidget(self.authorization_badge)

        header_layout.addLayout(top)

        self.position_label = QLabel("X —   Y —   Z —")
        self.position_label.setObjectName("subtitle")

        header_layout.addWidget(self.position_label)

        # Expose the existing safety authorization selector in this compact
        # control window. Its original confirmation callbacks remain intact.
        authorization_row = QHBoxLayout()
        authorization_row.setSpacing(5)

        authorization_label = QLabel("AUTH")
        authorization_label.setStyleSheet(
            "color:#94a3b8; font-weight:700;"
        )

        self.authorization_select = self.control.authorization_select
        self.authorization_select.setParent(header)
        self.authorization_select.setMinimumHeight(22)
        self.authorization_select.setMaximumHeight(25)
        self.authorization_select.setMinimumWidth(125)

        authorization_row.addWidget(authorization_label)
        authorization_row.addWidget(self.authorization_select, 1)

        header_layout.addLayout(authorization_row)

        outer.addWidget(header)

        # --------------------------------------------------
        # EXISTING LIVE CONTROL PANEL
        # --------------------------------------------------

        system_group = find_system_group(control)

        compact_controls(system_group)

        # Remove legacy width restriction.
        system_group.setMinimumWidth(0)
        system_group.setMaximumWidth(16777215)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        scroll.setWidget(system_group)

        outer.addWidget(scroll, 1)

        # --------------------------------------------------
        # SAFETY FOOTER
        # --------------------------------------------------

        footer = QLabel(
            "LOCKED = read-only.  "
            "STANDBY = controlled preparation.  "
            "OPERATIONAL = motion enabled."
        )
        footer.setWordWrap(True)
        footer.setStyleSheet(
            "color:#94a3b8; "
            "background:#0f172a; "
            "border:1px solid #334155; "
            "padding:5px;"
        )

        outer.addWidget(footer)

        self.setCentralWidget(central)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_status)
        self.timer.start(400)

        self.refresh_status()


    def refresh_status(self) -> None:
        connected = bool(self.control.system_connected)

        if connected:
            self.connection_badge.setText("CONNECTED")
            self.connection_badge.setStyleSheet(
                "background:#14532d; color:#dcfce7;"
            )
        else:
            self.connection_badge.setText("OFFLINE")
            self.connection_badge.setStyleSheet(
                "background:#7f1d1d; color:#fee2e2;"
            )

        authorization = str(
            getattr(self.control, "motion_authorization", "LOCKED")
        )

        self.authorization_badge.setText(authorization)

        if authorization == "OPERATIONAL":
            style = "background:#991b1b; color:#ffffff;"
        elif authorization == "STANDBY":
            style = "background:#92400e; color:#fef3c7;"
        else:
            style = "background:#334155; color:#e2e8f0;"

        self.authorization_badge.setStyleSheet(style)

        position = str(
            getattr(
                self.control,
                "last_system_payload",
                {},
            ).get("position", "")
        )

        if position:
            self.position_label.setText(position)


def main() -> int:
    app = QApplication(sys.argv)

    font = app.font()
    font.setPointSize(8)
    app.setFont(font)

    # Keep original controller alive but hidden.
    controller = OperatorWorkstation()

    controller.apply_motion_authorization(
        "LOCKED",
        confirm=False,
    )

    controller.hide()

    compact = CompactControlWindow(controller)

    screen = app.primaryScreen()
    if screen is not None:
        area = screen.availableGeometry()

        width = 390

        compact.setGeometry(
            area.x(),
            area.y(),
            width,
            area.height(),
        )

    compact.show()

    print("SPM_CONTROL_COMPACT=ACTIVE")
    print("CONTROL_WIDTH=390")
    print("MOTION_AUTHORIZATION=LOCKED")
    print("HARDWARE_LOGIC_CHANGED=NO")

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
