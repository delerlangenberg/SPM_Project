from PyQt5.QtWidgets import (
    QMainWindow, QMenuBar, QMenu, QAction, QDockWidget, QWidget,
    QVBoxLayout, QPushButton, QSpinBox, QDoubleSpinBox, QLabel,
    QMessageBox, QFileDialog
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPalette, QColor
import pyqtgraph as pg
import os

from interface.panels.z_regulation_gui import ZRegulationPanel
from interface.panels.ai_control_panel import AIControlPanel  # implement this
from interface.panels.simulation_panel import SimulationPanel  # implement this
from interface.panels.measurement_panel import MeasurementPanel  # scanning UI

from core.z_control.z_driver_arduino import ArduinoZDriver
from hardware.motor.motor_controller import MotorController
from ai.models.ml_model import MLModel

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SPM Control Interface")
        self.setGeometry(100, 100, 1400, 900)
        self._setup_dark_theme()

        self.setMenuBar(self._create_menu_bar())
        self._init_status_bar()
        self._init_dock_widgets()

    def _setup_dark_theme(self):
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(10, 10, 10))
        palette.setColor(QPalette.WindowText, QColor(230, 230, 230))
        self.setPalette(palette)

    def _create_menu_bar(self) -> QMenuBar:
        menu_bar = QMenuBar(self)

        # File menu
        file_menu = menu_bar.addMenu("&File")
        new_action = QAction("New Project", self)
        open_action = QAction("Open Project", self)
        save_action = QAction("Save Project", self)
        exit_action = QAction("Exit", self)
        file_menu.addActions([new_action, open_action, save_action])
        file_menu.addSeparator()
        file_menu.addAction(exit_action)

        # Control menu
        control_menu = menu_bar.addMenu("&Control")
        hardware_action = QAction("Hardware Control", self)
        scanning_action = QAction("Scanning Panel", self)
        zreg_action = QAction("Z Regulation", self)
        ai_action = QAction("AI Control", self)
        simulation_action = QAction("Simulation", self)
        control_menu.addActions([hardware_action, scanning_action, zreg_action, ai_action, simulation_action])

        # View menu for toggling docks
        view_menu = menu_bar.addMenu("&View")
        self.view_actions = {}
        for name in ['System Control', 'Live Plot', 'Z Regulation', 'AI Control', 'Simulation', 'Measurement']:
            action = QAction(name, self, checkable=True, checked=True)
            action.triggered.connect(self._toggle_dock_visibility)
            view_menu.addAction(action)
            self.view_actions[name] = action

        # Tools menu
        tools_menu = menu_bar.addMenu("&Tools")
        calibrate_action = QAction("Calibrate Z-Scanner", self)
        matcher_action = QAction("Pattern Matcher", self)
        trainer_action = QAction("ML Model Trainer", self)
        tools_menu.addActions([calibrate_action, matcher_action, trainer_action])

        # Help menu
        help_menu = menu_bar.addMenu("&Help")
        doc_action = QAction("Documentation", self)
        about_action = QAction("About", self)
        help_menu.addActions([doc_action, about_action])

        # Connect slots
        new_action.triggered.connect(self.new_project)
        open_action.triggered.connect(self.open_project)
        save_action.triggered.connect(self.save_project)
        exit_action.triggered.connect(self.close)
        hardware_action.triggered.connect(self.launch_hardware_controls)
        scanning_action.triggered.connect(lambda: self.view_actions['Measurement'].setChecked(True))
        zreg_action.triggered.connect(lambda: self.view_actions['Z Regulation'].setChecked(True))
        ai_action.triggered.connect(lambda: self.view_actions['AI Control'].setChecked(True))
        simulation_action.triggered.connect(lambda: self.view_actions['Simulation'].setChecked(True))

        calibrate_action.triggered.connect(self.calibrate_z_scanner)
        matcher_action.triggered.connect(self.launch_pattern_matcher)
        trainer_action.triggered.connect(self.launch_ml_trainer)
        doc_action.triggered.connect(self.open_documentation)
        about_action.triggered.connect(self.show_about_dialog)

        return menu_bar
    def _init_status_bar(self):
        self.statusBar().showMessage("Ready")
        self.connection_label = QLabel("Disconnected")
        self.statusBar().addPermanentWidget(self.connection_label)

    def _init_dock_widgets(self):
        # System Control Dock (connection button)
        self.sys_control_dock = QDockWidget("System Control", self)
        sys_widget = QWidget()
        sys_layout = QVBoxLayout()
        self.connect_button = QPushButton("Connect to System")
        self.connect_button.setStyleSheet("background-color: red; color: white;")
        self.connect_button.clicked.connect(self.toggle_system_connection)
        sys_layout.addWidget(self.connect_button)
        sys_widget.setLayout(sys_layout)
        self.sys_control_dock.setWidget(sys_widget)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.sys_control_dock)

        # Live Plot Dock
        self.plot_dock = QDockWidget("Live Scan Plot", self)
        plot_widget = pg.PlotWidget()
        plot_widget.setLabel('left', 'Z Signal', units='V')
        plot_widget.setLabel('bottom', 'Time', units='s')
        plot_widget.showGrid(x=True, y=True)
        self.plot_widget = plot_widget
        self.plot_dock.setWidget(plot_widget)
        self.plot_dock.setFeatures(QDockWidget.AllDockWidgetFeatures)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.plot_dock)

        # Z Regulation Panel Dock
        self.zreg_panel = ZRegulationPanel()
        self.zreg_dock = QDockWidget("Z Regulation", self)
        self.zreg_dock.setWidget(self.zreg_panel)
        self.addDockWidget(Qt.RightDockWidgetArea, self.zreg_dock)

        # AI Control Panel Dock
        self.ai_panel = AIControlPanel()
        self.ai_dock = QDockWidget("AI Control", self)
        self.ai_dock.setWidget(self.ai_panel)
        self.addDockWidget(Qt.RightDockWidgetArea, self.ai_dock)

        # Simulation Panel Dock
        self.sim_panel = SimulationPanel()
        self.sim_dock = QDockWidget("Simulation", self)
        self.sim_dock.setWidget(self.sim_panel)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.sim_dock)

        # Measurement (Scanning) Panel Dock
        self.measurement_panel = MeasurementPanel()
        self.measurement_dock = QDockWidget("Measurement", self)
        self.measurement_dock.setWidget(self.measurement_panel)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.measurement_dock)

    def _toggle_dock_visibility(self):
        action = self.sender()
        name = action.text()
        docks = {
            "System Control": self.sys_control_dock,
            "Live Plot": self.plot_dock,
            "Z Regulation": self.zreg_dock,
            "AI Control": self.ai_dock,
            "Simulation": self.sim_dock,
            "Measurement": self.measurement_dock,
        }
        dock = docks.get(name)
        if dock:
            dock.setVisible(action.isChecked())

    def toggle_system_connection(self):
        if self.connect_button.text() == "Connect to System":
            self.connect_button.setText("Connected")
            self.connect_button.setStyleSheet("background-color: green; color: white;")
            self.connection_label.setText("Connected")
            self.statusBar().showMessage("System connected")
            print("System connected (TODO: hardware handshake).")
        else:
            self.connect_button.setText("Connect to System")
            self.connect_button.setStyleSheet("background-color: red; color: white;")
            self.connection_label.setText("Disconnected")
            self.statusBar().showMessage("System disconnected")
            print("System disconnected (TODO: teardown).")

    # Project file handling
    def new_project(self):
        QMessageBox.information(self, "New Project", "Starting a new project.")

    def open_project(self):
        fname, _ = QFileDialog.getOpenFileName(self, "Open Project", "", "Project Files (*.spm)")
        if fname:
            QMessageBox.information(self, "Open Project", f"Project loaded: {os.path.basename(fname)}")

    def save_project(self):
        fname, _ = QFileDialog.getSaveFileName(self, "Save Project", "", "Project Files (*.spm)")
        if fname:
            QMessageBox.information(self, "Save Project", f"Project saved: {os.path.basename(fname)}")

    # Stub methods for control and tools
    def launch_hardware_controls(self):
        QMessageBox.information(self, "Hardware Control", "Hardware control panel to be implemented.")

    def calibrate_z_scanner(self):
        print("Z-Scanner calibration invoked. Implement hardware interface here.")

    def launch_pattern_matcher(self):
        QMessageBox.information(self, "Pattern Matcher", "Pattern matcher tool opened.")

    def launch_ml_trainer(self):
        QMessageBox.information(self, "ML Trainer", "Machine learning trainer started.")

    def open_documentation(self):
        QMessageBox.information(self, "Documentation", "Documentation viewer opened.")

    def show_about_dialog(self):
        QMessageBox.information(self, "About", "SPM Control Interface v1.0\nDeveloped by Delér Langenberg")
