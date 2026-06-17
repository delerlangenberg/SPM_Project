from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from core.system.hardware_information_exchange import (
    READONLY_HARDWARE_ACTIONS,
    action_commands,
    append_information_exchange_log,
    run_real_information_exchange,
)
from core.system.hardware_test_controls import (
    DEFAULT_STEP_MM,
    HARDWARE_TEST_ACTIONS,
    append_hardware_test_log,
    plan_hardware_test_action,
    run_hardware_test_action,
)


APP_VERSION = "v0.17.0"
APP_PHASE = "HT3 Hardware Test Console"
APP_TITLE = f"Educational SPM {APP_VERSION} - {APP_PHASE}"


class HardwareTestConsole(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.resize(980, 720)

        root = QVBoxLayout()
        root.addWidget(self.build_header())

        content = QHBoxLayout()
        content.addWidget(self.build_information_panel(), 1)
        content.addWidget(self.build_motion_panel(), 1)
        root.addLayout(content)

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setStyleSheet("font-family: Consolas, monospace;")
        root.addWidget(self.wrap_group("Operator Log", self.log), 1)

        self.setLayout(root)
        self.append_log(f"{APP_VERSION} loaded. Dry-run is default; no motion is armed.")
        self.preview_motion_action()

    def build_header(self) -> QGroupBox:
        box = QGroupBox("Workstation State")
        layout = QVBoxLayout()
        title = QLabel(f"{APP_VERSION} | {APP_PHASE}")
        title.setStyleSheet("font-weight: bold; font-size: 14px;")
        safety = QLabel(
            "Layer 1 hardware-test interface. Read-only commands are separate from supervised motion tests. "
            "Real motion stays locked until the operator enables it and types SUPERVISED."
        )
        safety.setWordWrap(True)
        safety.setStyleSheet("background: #fffde7; border: 1px solid #fbc02d; padding: 8px;")
        layout.addWidget(title)
        layout.addWidget(safety)
        box.setLayout(layout)
        return box

    def build_information_panel(self) -> QGroupBox:
        box = QGroupBox("1 Read-Only Hardware Information")
        layout = QVBoxLayout()

        self.info_action = QComboBox()
        self.info_action.addItems(["ALL", *READONLY_HARDWARE_ACTIONS.keys()])
        self.real_readonly_checkbox = QCheckBox("Run real read-only exchange on COM5")
        self.real_readonly_checkbox.setToolTip("Sends only M115/M105/M119/M114. No motion commands.")
        self.info_preview = QLabel("")
        self.info_preview.setWordWrap(True)
        self.info_preview.setStyleSheet("border: 1px solid #b0bec5; background: #ffffff; padding: 8px;")

        preview_btn = QPushButton("Preview Info Commands")
        preview_btn.clicked.connect(self.preview_information_action)
        run_btn = QPushButton("Run Information Exchange")
        run_btn.clicked.connect(self.run_information_action)

        layout.addWidget(QLabel("Action:"))
        layout.addWidget(self.info_action)
        layout.addWidget(self.real_readonly_checkbox)
        layout.addWidget(preview_btn)
        layout.addWidget(run_btn)
        layout.addWidget(self.info_preview)
        layout.addStretch()
        box.setLayout(layout)
        self.info_action.currentTextChanged.connect(self.preview_information_action)
        return box

    def build_motion_panel(self) -> QGroupBox:
        box = QGroupBox("2 Supervised Hardware Test Controls")
        layout = QVBoxLayout()

        form = QFormLayout()
        self.motion_action = QComboBox()
        self.motion_action.addItems(HARDWARE_TEST_ACTIONS)
        self.motion_action.currentTextChanged.connect(self.preview_motion_action)
        self.step_mm = QDoubleSpinBox()
        self.step_mm.setRange(0.1, 20.0)
        self.step_mm.setSingleStep(0.5)
        self.step_mm.setValue(DEFAULT_STEP_MM)
        self.step_mm.valueChanged.connect(self.preview_motion_action)
        form.addRow("Action:", self.motion_action)
        form.addRow("Step mm:", self.step_mm)
        layout.addLayout(form)

        self.supervised_motion_checkbox = QCheckBox("Enable supervised real motion")
        self.supervised_motion_checkbox.stateChanged.connect(self.preview_motion_action)
        self.confirm_text = QLineEdit()
        self.confirm_text.setPlaceholderText("type SUPERVISED to unlock real motion")
        self.confirm_text.textChanged.connect(self.preview_motion_action)
        layout.addWidget(self.supervised_motion_checkbox)
        layout.addWidget(self.confirm_text)

        self.motion_preview = QLabel("")
        self.motion_preview.setWordWrap(True)
        self.motion_preview.setStyleSheet("border: 1px solid #b0bec5; background: #ffffff; padding: 8px;")
        layout.addWidget(self.motion_preview)

        grid = QGridLayout()
        quick_actions = [
            "READ_POSITION",
            "SAFE_RETRACT",
            "SAFE_CENTER",
            "X_STEP_PLUS",
            "X_STEP_MINUS",
            "Y_STEP_PLUS",
            "Y_STEP_MINUS",
            "Z_STEP_UP",
            "Z_STEP_DOWN",
        ]
        for index, action in enumerate(quick_actions):
            button = QPushButton(action.replace("_", " "))
            button.clicked.connect(lambda _checked=False, selected=action: self.run_motion_action(selected))
            grid.addWidget(button, index // 3, index % 3)
        layout.addLayout(grid)
        layout.addStretch()
        box.setLayout(layout)
        return box

    def wrap_group(self, title: str, widget: QWidget) -> QGroupBox:
        group = QGroupBox(title)
        layout = QVBoxLayout()
        layout.addWidget(widget)
        group.setLayout(layout)
        return group

    def append_log(self, message: str) -> None:
        self.log.append(message)

    def preview_information_action(self) -> None:
        commands = action_commands(self.info_action.currentText())
        self.info_preview.setText(
            "Planned read-only commands:\n"
            + "\n".join(f"- {action}: {command}" for action, command in commands)
            + "\n\nNo motion commands are included."
        )

    def run_information_action(self) -> None:
        action = self.info_action.currentText()
        if not self.real_readonly_checkbox.isChecked():
            commands = action_commands(action)
            self.append_log("[INFO DRY RUN] " + ", ".join(f"{name}->{command}" for name, command in commands))
            self.preview_information_action()
            return

        try:
            results = run_real_information_exchange(action)
            log_path = append_information_exchange_log(results)
        except Exception as error:
            self.append_log(f"[INFO REAL] FAIL: {error}")
            QMessageBox.critical(self, "Read-only information failed", str(error))
            return

        for result in results:
            self.append_log(
                f"[INFO REAL] {result.action} {result.command} success={result.success}: "
                + " | ".join(result.response_lines)
            )
        self.append_log(f"[INFO REAL] log={log_path}")

    def real_motion_unlocked(self) -> bool:
        return self.supervised_motion_checkbox.isChecked() and self.confirm_text.text().strip() == "SUPERVISED"

    def preview_motion_action(self) -> None:
        try:
            plan = plan_hardware_test_action(self.motion_action.currentText(), step_mm=float(self.step_mm.value()))
            mode = "REAL MOTION UNLOCKED" if self.real_motion_unlocked() else "DRY RUN ONLY"
            self.motion_preview.setText(
                f"Mode: {mode}\n"
                f"Safety note: {plan.safety_note}\n"
                f"Moves hardware: {plan.moves_hardware}\n"
                "Commands:\n"
                + "\n".join(f"- {command}" for command in plan.commands)
            )
        except Exception as error:
            self.motion_preview.setText(f"Invalid motion plan: {error}")

    def run_motion_action(self, action: str | None = None) -> None:
        selected_action = action or self.motion_action.currentText()
        self.motion_action.setCurrentText(selected_action)
        execute = self.real_motion_unlocked()
        if execute:
            reply = QMessageBox.warning(
                self,
                "Confirm supervised real motion",
                (
                    f"Run {selected_action} on real hardware?\n\n"
                    "Continue only if the MK4S path is clear and you are watching the hardware."
                ),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                self.append_log(f"[MOTION REAL] Cancelled: {selected_action}")
                return

        result = run_hardware_test_action(
            selected_action,
            step_mm=float(self.step_mm.value()),
            execute=execute,
        )
        log_path = append_hardware_test_log(result)
        mode = "REAL" if execute else "DRY RUN"
        self.append_log(
            f"[MOTION {mode}] {result.action} success={result.success} | "
            f"commands={' | '.join(result.commands)} | before={result.before_position} | "
            f"after={result.after_position} | response={result.response} | log={log_path}"
        )
        if execute and not result.success:
            QMessageBox.critical(self, "Hardware test failed", result.response)
        self.preview_motion_action()


def main() -> int:
    app = QApplication(sys.argv)
    gui = HardwareTestConsole()
    gui.show()
    return app.exec_()


if __name__ == "__main__":
    raise SystemExit(main())
