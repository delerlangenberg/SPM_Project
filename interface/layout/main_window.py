import os

from PyQt5.QtWidgets import (
    QMainWindow, QMenuBar, QMenu, QAction, QDockWidget, QWidget,
    QVBoxLayout, QPushButton, QLabel, QMessageBox, QFileDialog,
    QComboBox
)

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPalette, QColor
import pyqtgraph as pg

from interface.panels.z_regulation_gui import ZRegulationPanel
from interface.panels.ai_control_panel import AIControlPanel
from interface.panels.simulation_panel import SimulationPanel
from interface.panels.measurement_panel import MeasurementPanel

from core.motion.prusa_gcode_backend import PrusaGcodeBackend
try:
    from serial.tools import list_ports
except Exception:  # pyserial not installed or unavailable
    list_ports = None
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.motion_backend = None
        self.is_connected = False
        ...
        self._init_dock_widgets()

    def _init_dock_widgets(self):
        ...
        self.addDockWidget(Qt.LeftDockWidgetArea, self.measurement_dock)

    def toggle_system_connection(self):
        # DISCONNECT
        if self.is_connected:
            try:
                if self.motion_backend is not None:
                    self.motion_backend.disconnect()
            except Exception as e:
                print(f"Disconnect warning: {e}")
            finally:
                self.motion_backend = None
                self.is_connected = False

            self.connect_button.setText("Connect to System")
            self.connect_button.setStyleSheet("")
            self.connection_label.setText("Disconnected")
            self.statusBar().showMessage("System disconnected")
            print("System disconnected (Prusa backend).")
            return

        # CONNECT
        port = self.port_selector.currentText()
        if not port:
            QMessageBox.warning(self, "No port selected", "No serial port selected.")
            return

        try:
            self.motion_backend = PrusaGcodeBackend(port=port)
            self.motion_backend.connect()
        except Exception as e:
            self.motion_backend = None
            self.is_connected = False
            self.statusBar().showMessage("System disconnected")
            print(f"System connect failed: {e}")
            return

        self.is_connected = True
        self.connect_button.setText("Connected")
        self.connect_button.setStyleSheet("background-color: green; color: white;")
        self.connection_label.setText("Connected")
        self.statusBar().showMessage("System connected")
        print(f"System connected (Prusa backend). port={self.motion_backend.port}")





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
        # System Control Dock (connection button + port selector)
        self.sys_control_dock = QDockWidget("System Control", self)
        sys_widget = QWidget()
        sys_layout = QVBoxLayout()

        # Port selector
        self.port_label = QLabel("Serial Port:")
        self.port_selector = QComboBox()
        self.refresh_ports_button = QPushButton("Refresh Ports")

        sys_layout.addWidget(self.port_label)
        sys_layout.addWidget(self.port_selector)
        sys_layout.addWidget(self.refresh_ports_button)

        # Connect button
        self.connect_button = QPushButton("Connect to System")
        self.connect_button.setStyleSheet("background-color: red; color: white;")
        self.connect_button.clicked.connect(self.toggle_system_connection)

        sys_layout.addWidget(self.connect_button)

        sys_widget.setLayout(sys_layout)
        self.sys_control_dock.setWidget(sys_widget)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.sys_control_dock)

        self.refresh_ports_button.clicked.connect(self.refresh_serial_ports)
        self.refresh_serial_ports()


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
            QMessageBox.warning(
                self,
            "Connection failed",
            f"Could not connect to the system on port: {port}\n\nError:\n{e}\n\n"
            "Hint: Click 'Refresh Ports' to find the correct COM port."
            )
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

    def show_available_ports(self):
        if list_ports is None:
            QMessageBox.warning(self, "Ports", "pyserial not available. Install: python -m pip install pyserial")
            return

        ports = list(list_ports.comports())
        if not ports:
            QMessageBox.information(self, "Ports", "No serial ports found.\n\nPlug in the printer via USB and try again.")
            return

        lines = [f"{p.device} — {p.description}" for p in ports]
        QMessageBox.information(self, "Ports", "Available serial ports:\n\n" + "\n".join(lines))

    def refresh_serial_ports(self):
        self.port_selector.clear()
        if list_ports is None:
            return
        ports = list_ports.comports()
        for p in ports:
            self.port_selector.addItem(p.device)

