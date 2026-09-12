from __future__ import annotations

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
os.chdir(PROJECT_ROOT)
os.environ["SPM_WEB_ALLOW_READONLY_HARDWARE"] = "1"

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
    QSplitter,
    QLayout,
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
                background: #070b14;
            }

            QWidget {
                font-family: 'Inter', 'Segoe UI', -apple-system, BlinkMacSystemFont, 'Ubuntu', sans-serif;
                font-size: 8.5pt;
                color: #e2e8f0;
            }

            QFrame#header {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #0f172a, stop:0.5 #0c1427, stop:1 #070e1c);
                border: 1px solid #1e293b;
                border-top: 3px solid #00f0ff;
                border-radius: 8px;
            }

            QLabel#title {
                color: #f8fafc;
                font-size: 11pt;
                font-weight: 900;
                letter-spacing: 0.8px;
            }

            QLabel#subtitle {
                color: #38bdf8;
                font-size: 7.5pt;
                font-weight: 700;
                letter-spacing: 0.4px;
            }

            QFrame#positionFrame {
                background: #020617;
                border: 1px solid #0284c7;
                border-radius: 6px;
                padding: 4px 8px;
            }

            QLabel#positionLabel {
                color: #00f0ff;
                font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
                font-size: 9pt;
                font-weight: 800;
                letter-spacing: 0.8px;
            }

            QLabel#connectionBadge {
                padding: 4px 10px;
                border-radius: 12px;
                font-weight: 800;
                font-size: 7.5pt;
                letter-spacing: 0.6px;
            }

            QLabel#authBadge {
                padding: 4px 10px;
                border-radius: 12px;
                font-weight: 800;
                font-size: 7.5pt;
                letter-spacing: 0.6px;
            }

            QGroupBox {
                background: #0b1120;
                border: 1px solid #1e293b;
                border-left: 2px solid #38bdf8;
                border-radius: 8px;
                margin-top: 14px;
                padding-top: 12px;
                font-weight: 700;
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0px 8px;
                color: #38bdf8;
                font-size: 8pt;
                font-weight: 800;
                letter-spacing: 0.8px;
                background: #070b14;
                border: 1px solid #1e293b;
                border-radius: 4px;
            }

            QPushButton {
                min-height: 25px;
                max-height: 28px;
                padding: 3px 10px;
                border-radius: 5px;
                font-weight: 700;
                font-size: 8pt;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #1e293b, stop:1 #0f172a);
                color: #f1f5f9;
                border: 1px solid #334155;
            }

            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #334155, stop:1 #1e293b);
                border: 1px solid #00f0ff;
                color: #ffffff;
            }

            QPushButton:pressed {
                background: #020617;
                border: 1px solid #0284c7;
            }

            QPushButton:disabled {
                background: #0b1120;
                color: #475569;
                border: 1px solid #1e293b;
            }

            QComboBox {
                background: #0b1120;
                color: #f8fafc;
                border: 1px solid #334155;
                border-radius: 5px;
                padding: 2px 8px;
                font-weight: 700;
                min-height: 26px;
            }

            QComboBox:hover {
                border: 1px solid #00f0ff;
            }

            QComboBox:focus {
                border: 1px solid #38bdf8;
            }

            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 24px;
                border-left: 1px solid #334155;
                border-top-right-radius: 4px;
                border-bottom-right-radius: 4px;
                background: #1e293b;
            }

            QComboBox QAbstractItemView {
                background-color: #0b1120;
                color: #f8fafc;
                selection-background-color: #0284c7;
                selection-color: #ffffff;
                border: 1px solid #00f0ff;
                border-radius: 4px;
                outline: none;
                padding: 4px;
            }

            QComboBox QAbstractItemView::item {
                min-height: 28px;
                padding: 5px 10px;
                color: #f8fafc;
                border-radius: 3px;
            }

            QComboBox QAbstractItemView::item:selected {
                background-color: #0284c7;
                color: #ffffff;
                font-weight: 800;
            }

            QComboBox QAbstractItemView::item:hover {
                background-color: #0369a1;
                color: #ffffff;
            }

            QSpinBox, QDoubleSpinBox, QLineEdit {
                background: #0b1120;
                color: #f8fafc;
                border: 1px solid #334155;
                border-radius: 4px;
                min-height: 23px;
                max-height: 26px;
                padding: 1px 6px;
                font-weight: 600;
            }

            QSpinBox:focus, QDoubleSpinBox:focus, QLineEdit:focus {
                border: 1px solid #00f0ff;
                background: #020617;
            }

            QScrollArea {
                border: none;
                background: transparent;
            }

            QScrollBar:vertical {
                border: none;
                background: #070b14;
                width: 7px;
                border-radius: 3px;
            }

            QScrollBar::handle:vertical {
                background: #1e293b;
                min-height: 20px;
                border-radius: 3px;
            }

            QScrollBar::handle:vertical:hover {
                background: #00f0ff;
            }

            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
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

        # High-tech OLED coordinate HUD
        pos_frame = QFrame()
        pos_frame.setObjectName("positionFrame")
        pos_layout = QHBoxLayout(pos_frame)
        pos_layout.setContentsMargins(6, 4, 6, 4)
        pos_layout.setSpacing(6)

        pos_title = QLabel("POS [mm]")
        pos_title.setStyleSheet("color:#64748b; font-size:7pt; font-weight:800; letter-spacing:0.5px;")
        pos_layout.addWidget(pos_title)

        self.position_label = QLabel("X: ---.--   Y: ---.--   Z: ---.--")
        self.position_label.setObjectName("positionLabel")
        self.position_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        pos_layout.addWidget(self.position_label, 1)

        header_layout.addWidget(pos_frame)

        # Expose the existing safety authorization selector in this compact
        # control window. Its original confirmation callbacks remain intact.
        authorization_row = QHBoxLayout()
        authorization_row.setSpacing(6)

        authorization_label = QLabel("SAFETY")
        authorization_label.setStyleSheet(
            "color:#38bdf8; font-weight:800; font-size:7.5pt; letter-spacing:0.5px;"
        )

        self.authorization_select = self.control.authorization_select
        self.authorization_select.setParent(header)
        self.authorization_select.setMinimumHeight(28)
        self.authorization_select.setMaximumHeight(32)
        self.authorization_select.setMinimumWidth(165)
        self.authorization_select.setMinimumContentsLength(12)
        self.authorization_select.setSizeAdjustPolicy(
            QComboBox.SizeAdjustPolicy.AdjustToContents
        )
        self.authorization_select.view().setMinimumWidth(200)
        self.authorization_select.view().setStyleSheet(
            "background-color: #0b1120; color: #f8fafc; selection-background-color: #0284c7; selection-color: #ffffff; padding: 4px; border: 1px solid #00f0ff;"
        )
        # Authorization selector is active for operator control
        self.authorization_select.setEnabled(True)
        authorization_row.addWidget(authorization_label)
        authorization_row.addWidget(self.authorization_select, 1)

        header_layout.addLayout(authorization_row)

        outer.addWidget(header)

        # --------------------------------------------------
        # EXISTING LIVE CONTROL PANEL
        # --------------------------------------------------

        system_group = find_system_group(control)

        compact_controls(system_group)

        # Style action buttons with distinct high-tech scientific instrument colors
        for button in system_group.findChildren(QPushButton):
            text = button.text().replace("&", "").strip().casefold()
            if text == "e-stop":
                button.setText("🛑 Stop sequence")
                button.setToolTip(
                    "Software stop request only. Does not guarantee interruption "
                    "of an executing printer command. Not a hardware emergency stop."
                )
                button.setStyleSheet(
                    "QPushButton { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #dc2626, stop:1 #991b1b);"
                    "color: #ffffff; font-weight: 800; border: 1px solid #f87171; border-radius: 5px; min-height: 26px; }"
                    "QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ef4444, stop:1 #b91c1c); border: 1px solid #ffffff; }"
                    "QPushButton:pressed { background: #7f1d1d; }"
                )
            elif "connect" in text:
                button.setStyleSheet(
                    "QPushButton { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #059669, stop:1 #047857);"
                    "color: #ffffff; font-weight: 800; border: 1px solid #34d399; border-radius: 5px; min-height: 26px; }"
                    "QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #10b981, stop:1 #059669); border: 1px solid #a7f3d0; }"
                    "QPushButton:pressed { background: #064e3b; }"
                )
            elif "diagnos" in text:
                button.setStyleSheet(
                    "QPushButton { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #2563eb, stop:1 #1d4ed8);"
                    "color: #ffffff; font-weight: 700; border: 1px solid #60a5fa; border-radius: 5px; min-height: 26px; }"
                    "QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #3b82f6, stop:1 #2563eb); border: 1px solid #93c5fd; }"
                    "QPushButton:pressed { background: #1e3a8a; }"
                )
            elif text == "refresh ports":
                button.setText("🔄 Refresh Ports")
                button.setFlat(False)
                button.setStyleSheet(
                    "QPushButton { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #334155, stop:1 #1e293b);"
                    "color: #38bdf8; font-weight: 700; border: 1px solid #475569; border-radius: 5px; min-height: 26px; }"
                    "QPushButton:hover { background: #475569; border: 1px solid #38bdf8; color: #ffffff; }"
                    "QPushButton:pressed { background: #0f172a; }"
                )
                button.setToolTip(
                    "Refresh detected serial ports. Does not connect or move hardware."
                )
            elif "calibrat" in text:
                button.setEnabled(False)
                button.setToolTip("Blocked following unsafe Z homing incident.")

        # Remove legacy width restriction.
        system_group.setMinimumWidth(0)
        system_group.setMaximumWidth(16777215)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        scroll.setWidget(system_group)

        # SPM_SLIDABLE_LOGS
        editors = [
            w for w in system_group.findChildren(QWidget)
            if isinstance(w, (QTextEdit, QPlainTextEdit))
        ]

        # SPM_SUMMARY_IN_LOG_PANEL
        summaries = [
            label for label in system_group.findChildren(QLabel)
            if "system: not connected" in label.text().casefold()
        ]
        for label in summaries:
            label.setWordWrap(True)
            label.setAlignment(
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop
            )
        editors = summaries + editors

        self.content_splitter = QSplitter(Qt.Orientation.Vertical)
        self.content_splitter.setHandleWidth(8)
        self.content_splitter.setStyleSheet(
            "QSplitter::handle { background:#475569; }"
            "QSplitter::handle:hover { background:#60a5fa; }"
        )
        self.content_splitter.addWidget(scroll)
        self.content_splitter.setCollapsible(0, False)
        scroll.setMinimumHeight(180)

        self.log_panel = QWidget()
        log_layout = QVBoxLayout(self.log_panel)
        log_layout.setContentsMargins(0, 0, 0, 0)
        log_layout.setSpacing(3)

        self.log_splitter = QSplitter(Qt.Orientation.Vertical)
        self.log_splitter.setHandleWidth(6)
        for editor in editors:
            for layout in system_group.findChildren(QLayout):
                layout.removeWidget(editor)
            if system_group.layout() is not None:
                system_group.layout().removeWidget(editor)
            editor.setMinimumHeight(0)
            editor.setMaximumHeight(16777215)
            editor.setSizePolicy(
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Expanding,
            )
            editor.setStyleSheet(
                "background:#0f172a; color:#e2e8f0;"
                "border:1px solid #475569;"
                "selection-background-color:#2563eb;"
            )
            if isinstance(editor, QLabel):
                summary_scroll = QScrollArea()
                summary_scroll.setWidgetResizable(True)
                summary_scroll.setMinimumHeight(0)
                summary_scroll.setWidget(editor)
                self.log_splitter.addWidget(summary_scroll)
            else:
                self.log_splitter.addWidget(editor)

        for label in system_group.findChildren(QLabel):
            if label.text().strip().rstrip(":").lower() == "connection activity":
                label.hide()

        # SPM_PACK_CONTROLS_TOP
        # Keep the control group at its natural height inside the scroll area.
        scroll.takeWidget()
        controls_container = QWidget()
        controls_layout = QVBoxLayout(controls_container)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(0)
        system_group.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Maximum,
        )
        if system_group.layout() is not None:
            system_group.layout().setAlignment(Qt.AlignmentFlag.AlignTop)
        for label in system_group.findChildren(QLabel):
            label.setSizePolicy(
                QSizePolicy.Policy.Preferred,
                QSizePolicy.Policy.Maximum,
            )
        controls_layout.addWidget(system_group)
        controls_layout.addStretch(1)
        scroll.setWidget(controls_container)

        log_layout.addWidget(self.log_splitter)
        self.content_splitter.addWidget(self.log_panel)
        self.content_splitter.setCollapsible(1, True)
        self.content_splitter.setStretchFactor(0, 1)
        self.content_splitter.setStretchFactor(1, 0)
        outer.addWidget(self.content_splitter, 1)

        self.logs_toggle = QPushButton("Hide logs")
        self.logs_toggle.setCheckable(True)
        self.logs_toggle.setChecked(True)

        def toggle_logs(visible):
            if not visible:
                self._saved_log_sizes = self.content_splitter.sizes()
            self.log_panel.setVisible(visible)
            self.logs_toggle.setText("Hide logs" if visible else "Show logs")
            if visible:
                sizes = getattr(self, "_saved_log_sizes", [500, 180])
                self.content_splitter.setSizes(
                    sizes if sizes[-1] > 0 else [500, 180]
                )

        self.logs_toggle.toggled.connect(toggle_logs)
        outer.addWidget(self.logs_toggle)

        def size_logs():
            height = max(self.content_splitter.height(), 360)
            self.content_splitter.setSizes([max(180, height - 180), 180])
            self.log_splitter.setSizes([110, 70])

        QTimer.singleShot(0, size_logs)


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


    # SPM_COMPACT_CLOSE_LIFECYCLE
    def closeEvent(self, event) -> None:
        if getattr(self.control, "_safe_close_approved", False):
            self.timer.stop()
            event.accept()
            return
        event.ignore()
        if not getattr(self.control, "_safe_close_in_progress", False):
            self.control.request_safe_exit()

    def refresh_status(self) -> None:
        if getattr(self.control, "_safe_close_approved", False):
            self.timer.stop()
            self.close()
            app = QApplication.instance()
            if app is not None:
                app.quit()
            return
        connected = bool(self.control.system_connected)

        if connected:
            self.connection_badge.setText("● ONLINE")
            self.connection_badge.setStyleSheet(
                "background: #064e3b; color: #6ee7b7; border: 1px solid #10b981; font-weight: 800;"
            )
            if hasattr(self.control, "connect_button"):
                self.control.connect_button.setStyleSheet(
                    "QPushButton { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #b45309, stop:1 #78350f);"
                    "color: #ffffff; font-weight: 800; border: 1px solid #f59e0b; border-radius: 5px; min-height: 26px; }"
                    "QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #d97706, stop:1 #92400e); border: 1px solid #fde68a; }"
                    "QPushButton:pressed { background: #451a03; }"
                )
        else:
            self.connection_badge.setText("○ OFFLINE")
            self.connection_badge.setStyleSheet(
                "background: #450a0a; color: #fca5a5; border: 1px solid #991b1b; font-weight: 800;"
            )
            if hasattr(self.control, "connect_button"):
                self.control.connect_button.setStyleSheet(
                    "QPushButton { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #059669, stop:1 #047857);"
                    "color: #ffffff; font-weight: 800; border: 1px solid #34d399; border-radius: 5px; min-height: 26px; }"
                    "QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #10b981, stop:1 #059669); border: 1px solid #a7f3d0; }"
                    "QPushButton:pressed { background: #064e3b; }"
                )

        authorization = str(
            getattr(self.control, "motion_authorization", "LOCKED")
        )

        if authorization == "OPERATIONAL":
            self.authorization_badge.setText("⚠️ OPERATIONAL")
            style = "background: #450a0a; color: #fca5a5; border: 1px solid #ef4444; font-weight: 800;"
        elif authorization == "STANDBY":
            self.authorization_badge.setText("⚡ STANDBY")
            style = "background: #451a03; color: #fde68a; border: 1px solid #f59e0b; font-weight: 800;"
        else:
            self.authorization_badge.setText("🔒 LOCKED")
            style = "background: #0f172a; color: #38bdf8; border: 1px solid #0284c7; font-weight: 800;"

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
        else:
            self.position_label.setText("X: ---.--   Y: ---.--   Z: ---.--")

        # Keep action buttons in sync with connection and authorization
        self.control.update_authorization_controls()


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
