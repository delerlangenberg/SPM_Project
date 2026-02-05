import os

from PyQt5.QtWidgets import (
    QMainWindow, QMenuBar, QMenu, QAction, QDockWidget, QWidget,
    QVBoxLayout, QPushButton, QLabel, QMessageBox, QFileDialog
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPalette, QColor
import pyqtgraph as pg

from interface.panels.z_regulation_gui import ZRegulationPanel
from interface.panels.ai_control_panel import AIControlPanel
from interface.panels.simulation_panel import SimulationPanel
from interface.panels.measurement_panel import MeasurementPanel

from core.motion.prusa_gcode_backend import PrusaGcodeBackend


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Connection state
        self.is_connected = False
        self.motion_backend = None

        self.setWindowTitle("SPM Control Interface")
        self.setGeometry(100, 100, 1400, 900)
        self._setup_dark_theme()
        self.setMenuBar(self._create_menu_bar())
        self._init_status_bar()
        self._init_dock_widgets()

    # ---------- UI setup ----------

    def _setup_dark_theme(self):
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(10, 10, 10))
        palette.setColor(QPalette.WindowText, QColor(230, 230, 230))
        self.setPalette(palette)

    def _create_menu_bar(self) -> QMenuBar:
        menu_bar = QMenuBar(self)

        file_menu = menu_bar.addMenu("&File")
        new_action = QAction("New Project", self)
        open_action = QAction("Open Project", self)
        save_action = QAction("Save Project", self)
        exit_action = QAction("Exit", self)
        file_menu.addActions([new_action, open_action, save_action])
        file_menu.addSeparator()
        file_menu.addAction(exit_action)

        view_menu = menu_bar.addMenu("&View")
        self.view_actions = {}
        for name in ["System Control", "Live Plot", "Z Regulation", "AI Control", "Simulation", "Measurement"]:
            action = QAction(name, self, checkable=True, checked=True)
            action.triggered.connect(self._toggle_dock_visibility)
            view_menu.addAction(action)
            self.view_actions[name] = action

        new_action.triggered.connect(self.new_project)
        open_action.triggered.connect(self.open_project)
        save_action.triggered.connect(self.save_project)
        exit_action.triggered.connect(self.close)

        return menu_bar

    def _init_status_bar(self):
        self.statusBar().showMessage("Ready")
        self.connection_label = QLabel("Disconnected")
        self.statusBar().addPermanentWidget(self.connection_label)

    def _init_dock_widgets(self):
        # System Control
        self.sys_control_dock = QDockWidget("System Control", self)
        sys_widget = QWidget()
        layout = QVBoxLayout()

        self.connect_button = QPushButton("Connect to System")
        self.connect_button.setStyleSheet("background-color: red; color: white;")
        self.connect_button.clicked.connect(self.toggle_system_connection)

        layout.addWidget(self.connect_button)
        sys_widget.setLayout(layout)
        self.sys_control_dock.setWidget(sys_widget)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.sys_control_dock)

        # Live plot
        self.plot_dock = QDockWidget("Live Scan Plot", self)
        plot = pg.PlotWidget()
        plot.setLabel("left", "Z Signal")
        plot.setLabel("bottom", "Time")
        plot.showGrid(x=True, y=True)
        self.plot_dock.setWidget(plot)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.plot_dock)

        # Other docks
        self.zreg_dock = QDockWidget("Z Regulation", self)
        self.zreg_dock.setWidget(ZRegulationPanel())
        self.addDockWidget(Qt.RightDockWidgetArea, self.zreg_dock)

        self.ai_dock = QDockWidget("AI Control", self)
        self.ai_dock.setWidget(AIControlPanel())
        self.addDockWidget(Qt.RightDockWidgetArea, self.ai_dock)

        self.sim_dock = QDockWidget("Simulation", self)
        self.sim_dock.setWidget(SimulationPanel())
        self.addDockWidget(Qt.LeftDockWidgetArea, self.sim_dock)

        self.measurement_dock = QDockWidget("Measurement", self)
        self.measurement_dock.setWidget(MeasurementPanel())
        self.addDockWidget(Qt.LeftDockWidgetArea, self.measurement_dock)

    def _toggle_dock_visibility(self):
        action = self.sender()
        docks = {
            "System Control": self.sys_control_dock,
            "Live Plot": self.plot_dock,
            "Z Regulation": self.zreg_dock,
            "AI Control": self.ai_dock,
            "Simulation": self.sim_dock,
            "Measurement": self.measurement_dock,
        }
        dock = docks.get(action.text())
        if dock:
            dock.setVisible(action.isChecked())

    # ---------- Connection logic ----------

    def toggle_system_connection(self):
        if self.is_connected:
            if self.motion_backend:
                self.motion_backend.disconnect()
            self.motion_backend = None
            self.is_connected = False
            self.connect_button.setText("Connect to System")
            self.connect_button.setStyleSheet("background-color: red; color: white;")
            self.connection_label.setText("Disconnected")
            self.statusBar().showMessage("System disconnected")
            print("System disconnected (Prusa backend)")
            return

        port = os.environ.get("SPM_MOTION_PORT", "COM5")
        try:
            self.motion_backend = PrusaGcodeBackend(port=port)
            self.motion_backend.connect()
        except Exception as e:
            self.motion_backend = None
            self.statusBar().showMessage("System disconnected")
            print(f"System connect failed: {e}")
            return

        self.is_connected = True
        self.connect_button.setText("Connected")
        self.connect_button.setStyleSheet("background-color: green; color: white;")
        self.connection_label.setText("Connected")
        self.statusBar().showMessage("System connected")
        print(f"System connected (Prusa backend). port={port}")

    # ---------- Project / tools ----------

    def new_project(self):
        QMessageBox.information(self, "New Project", "Starting a new project.")

    def open_project(self):
        fname, _ = QFileDialog.getOpenFileName(self, "Open Project", "", "Project Files (*.spm)")
        if fname:
            QMessageBox.information(self, "Open Project", fname)

    def save_project(self):
        fname, _ = QFileDialog.getSaveFileName(self, "Save Project", "", "Project Files (*.spm)")
        if fname:
            QMessageBox.information(self, "Save Project", fname)
