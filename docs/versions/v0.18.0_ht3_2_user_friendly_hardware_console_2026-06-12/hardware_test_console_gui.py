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


APP_VERSION = "v0.18.0"
APP_PHASE = "HT3.2 User-Friendly Hardware Test Console"
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
        self.append_log(f"{APP_VERSION} loaded. Preview mode is default; no motion is armed.")
        self.preview_motion_action()

    def build_header(self) -> QGroupBox:
        box = QGroupBox("Workstation State")
        layout = QVBoxLayout()
        header_row = QHBoxLayout()
        title = QLabel(f"{APP_VERSION} | {APP_PHASE}")
        title.setStyleSheet("font-weight: bold; font-size: 14px;")
        about_btn = QPushButton("About")
        about_btn.clicked.connect(self.show_about)
        header_row.addWidget(title, 1)
        header_row.addWidget(about_btn, 0)
        safety = QLabel(
            "Layer 1 hardware-test interface. Read-only commands are separate from supervised motion tests. "
            "Real motion stays locked until the operator enables it and types SUPERVISED."
        )
        safety.setWordWrap(True)
        safety.setStyleSheet("background: #fffde7; border: 1px solid #fbc02d; padding: 8px;")
        layout.addLayout(header_row)
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

        self.motion_lock_label = QLabel("")
        self.motion_lock_label.setWordWrap(True)
        self.motion_lock_label.setStyleSheet("font-weight: bold; border: 1px solid #b0bec5; padding: 8px;")
        layout.addWidget(self.motion_lock_label)

        self.motion_preview = QLabel("")
        self.motion_preview.setWordWrap(True)
        self.motion_preview.setStyleSheet("border: 1px solid #b0bec5; background: #ffffff; padding: 8px;")
        layout.addWidget(self.motion_preview)

        action_row = QHBoxLayout()
        preview_selected_btn = QPushButton("Preview Selected Command")
        preview_selected_btn.clicked.connect(lambda: self.run_motion_action(self.motion_action.currentText(), execute=False))
        execute_selected_btn = QPushButton("EXECUTE SELECTED ON REAL HARDWARE")
        execute_selected_btn.setStyleSheet("font-weight: bold; background: #b71c1c; color: white;")
        execute_selected_btn.clicked.connect(lambda: self.run_motion_action(self.motion_action.currentText(), execute=True))
        action_row.addWidget(preview_selected_btn)
        action_row.addWidget(execute_selected_btn)
        layout.addLayout(action_row)

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
            button = QPushButton("Preview " + action.replace("_", " "))
            button.clicked.connect(lambda _checked=False, selected=action: self.run_motion_action(selected, execute=False))
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
            mode = "REAL MOTION UNLOCKED" if self.real_motion_unlocked() else "REAL MOTION LOCKED - preview only"
            if self.real_motion_unlocked():
                self.motion_lock_label.setText("REAL MOTION UNLOCKED: selected command can be executed after confirmation popup.")
                self.motion_lock_label.setStyleSheet("font-weight: bold; color: #b71c1c; border: 1px solid #b71c1c; padding: 8px;")
            else:
                self.motion_lock_label.setText(
                    "REAL MOTION LOCKED: buttons only preview commands. To move hardware, check the box and type SUPERVISED."
                )
                self.motion_lock_label.setStyleSheet("font-weight: bold; color: #2e7d32; border: 1px solid #2e7d32; padding: 8px;")
            self.motion_preview.setText(
                f"Mode: {mode}\n"
                f"Safety note: {plan.safety_note}\n"
                f"Moves hardware: {plan.moves_hardware}\n"
                "Commands:\n"
                + "\n".join(f"- {command}" for command in plan.commands)
            )
        except Exception as error:
            self.motion_preview.setText(f"Invalid motion plan: {error}")

    def run_motion_action(self, action: str | None = None, *, execute: bool = False) -> None:
        selected_action = action or self.motion_action.currentText()
        self.motion_action.setCurrentText(selected_action)
        if execute:
            if not self.real_motion_unlocked():
                self.append_log(
                    f"[MOTION LOCKED] {selected_action} not sent. Check Enable supervised real motion and type SUPERVISED."
                )
                QMessageBox.information(
                    self,
                    "Real motion locked",
                    (
                        "The hardware did not move because real motion is locked.\n\n"
                        "To execute on hardware:\n"
                        "1. Check Enable supervised real motion.\n"
                        "2. Type SUPERVISED.\n"
                        "3. Press EXECUTE SELECTED ON REAL HARDWARE.\n"
                        "4. Confirm the popup while watching the MK4S."
                    ),
                )
                self.preview_motion_action()
                return
            reply = QMessageBox.warning(
                self,
                "Confirm supervised real motion",
                (
                    f"Run {selected_action} on real hardware?\n\n"
                    "Continue only if the MK4S path is clear and you are watching the hardware."
                ),
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if reply != QMessageBox.Yes:
                self.append_log(f"[MOTION REAL] Cancelled: {selected_action}")
                return

        result = run_hardware_test_action(
            selected_action,
            step_mm=float(self.step_mm.value()),
            execute=execute,
        )
        log_path = append_hardware_test_log(result)
        mode = "REAL" if execute else "PREVIEW"
        self.append_log(
            f"[MOTION {mode}] {result.action} success={result.success} | "
            f"commands={' | '.join(result.commands)} | before={result.before_position} | "
            f"after={result.after_position} | response={result.response} | log={log_path}"
        )
        if execute and not result.success:
            QMessageBox.critical(self, "Hardware test failed", result.response)
        self.preview_motion_action()

    def show_about(self) -> None:
        QMessageBox.information(
            self,
            "About Educational SPM",
            (
                f"{APP_TITLE}\n\n"
                "Hardware Test Layer for the Educational SPM project.\n"
                "Preview mode is default. Real motion requires supervised unlock and confirmation."
            ),
        )


def main() -> int:
    app = QApplication(sys.argv)
    gui = HardwareTestConsole()
    gui.show()
    return app.exec_()


if __name__ == "__main__":
    raise SystemExit(main())
