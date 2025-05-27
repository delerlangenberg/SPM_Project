from PyQt5.QtWidgets import (
    QMenuBar, QMenu, QAction, QMainWindow, QDockWidget, QWidget, QVBoxLayout,
    QLabel, QComboBox, QSpinBox, QGroupBox, QCheckBox, QDoubleSpinBox,
    QPushButton, QFileDialog, QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPalette, QColor
from typing import TYPE_CHECKING
import pyqtgraph as pg  # Added for live plotting
import os

if TYPE_CHECKING:
    from PyQt5.QtWidgets import QMainWindow

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SPM Control Interface")
        self.setGeometry(100, 100, 1200, 800)
        self._setup_ui()

    def _setup_ui(self):
        self._setup_palette()
        self.setMenuBar(self._create_menu_bar())
        self._init_dock_widgets()
        self.show()

    def _setup_palette(self):
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor("grey"))
        palette.setColor(QPalette.WindowText, QColor("white"))
        self.setPalette(palette)

    def _create_menu_bar(self) -> QMenuBar:
        menu_bar = QMenuBar(self)

        # File Menu
        file_menu = QMenu("File", self)
        new_action = QAction("New Project", self)
        open_action = QAction("Open Project", self)
        save_action = QAction("Save Project", self)
        exit_action = QAction("Exit", self)
        file_menu.addActions([new_action, open_action, save_action])
        file_menu.addSeparator()
        file_menu.addAction(exit_action)
        menu_bar.addMenu(file_menu)

        # Control Menu
        control_menu = QMenu("Control", self)
        hardware_action = QAction("Hardware Control", self)
        scanning_action = QAction("Scanning", self)
        zreg_action = QAction("Z Regulation", self)
        control_menu.addActions([hardware_action, scanning_action, zreg_action])
        menu_bar.addMenu(control_menu)

        # View Menu
        view_menu = QMenu("View", self)
        live_plot_action = QAction("Live Plot", self)
        topo_view_action = QAction("Topograph Viewer", self)
        diagnostics_action = QAction("System Diagnostics", self)
        view_menu.addActions([live_plot_action, topo_view_action, diagnostics_action])
        menu_bar.addMenu(view_menu)

        # Tools Menu
        tools_menu = QMenu("Tools", self)
        calibrate_action = QAction("Calibrate Z-Scanner", self)
        matcher_action = QAction("Pattern Matcher", self)
        trainer_action = QAction("ML Model Trainer", self)
        tools_menu.addActions([calibrate_action, matcher_action, trainer_action])
        menu_bar.addMenu(tools_menu)

        # Simulation Menu
        sim_menu = QMenu("Simulation", self)
        toggle_sim_action = QAction("Enable Simulation Mode", self, checkable=True)
        dummy_signal_action = QAction("Inject Dummy Signal", self)
        sim_menu.addActions([toggle_sim_action, dummy_signal_action])
        menu_bar.addMenu(sim_menu)

        # Help Menu
        help_menu = QMenu("Help", self)
        doc_action = QAction("Documentation", self)
        about_action = QAction("About", self)
        help_menu.addActions([doc_action, about_action])
        menu_bar.addMenu(help_menu)

        # Connect Actions to Slots
        toggle_sim_action.triggered.connect(self.toggle_simulation_mode)
        dummy_signal_action.triggered.connect(self.inject_dummy_signal)
        new_action.triggered.connect(self.new_project)
        open_action.triggered.connect(self.open_project)
        save_action.triggered.connect(self.save_project)
        exit_action.triggered.connect(self.close)
        hardware_action.triggered.connect(self.launch_hardware_controls)
        scanning_action.triggered.connect(self.launch_scanning_panel)
        zreg_action.triggered.connect(self.launch_z_regulation_gui)
        live_plot_action.triggered.connect(self.launch_live_plot)
        topo_view_action.triggered.connect(self.launch_topograph_viewer)
        diagnostics_action.triggered.connect(self.launch_system_diagnostics)
        calibrate_action.triggered.connect(self.calibrate_z_scanner)
        matcher_action.triggered.connect(self.launch_pattern_matcher)
        trainer_action.triggered.connect(self.launch_ml_trainer)
        doc_action.triggered.connect(self.open_documentation)
        about_action.triggered.connect(self.show_about_dialog)

        return menu_bar
    def _init_dock_widgets(self):
        # --- System Control Dock ---
        # [unchanged code]

        # --- Z-Regulation Dock ---
        # [unchanged code]

        # --- Live Plot Dock with pyqtgraph ---
        self.plot_dock = QDockWidget("Live Scan Plot", self)
        plot_widget = pg.PlotWidget()
        plot_widget.setLabel('left', 'Z Signal', units='V')
        plot_widget.setLabel('bottom', 'Time', units='s')
        plot_widget.showGrid(x=True, y=True)
        self.plot_widget = plot_widget  # Save reference for future updates
        self.plot_dock.setWidget(plot_widget)
        self.plot_dock.setFeatures(QDockWidget.AllDockWidgetFeatures)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.plot_dock)

    def new_project(self):
        QMessageBox.information(self, "New Project", "Starting a new project.")

    def open_project(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Open Project", "", "Project Files (*.spm)")
        if file_name:
            QMessageBox.information(self, "Open Project", f"Project loaded: {os.path.basename(file_name)}")

    def save_project(self):
        file_name, _ = QFileDialog.getSaveFileName(self, "Save Project", "", "Project Files (*.spm)")
        if file_name:
            QMessageBox.information(self, "Save Project", f"Project saved to: {os.path.basename(file_name)}")

    def launch_hardware_controls(self):
        print("Launching hardware control panel... (TODO: link to real widget)")

    def launch_scanning_panel(self):
        print("Launching scanning panel with real UI...")
        scan_dock = QDockWidget("Scanning Panel", self)
        scan_widget = QWidget()
        scan_layout = QVBoxLayout()

        self.x_range = QSpinBox()
        self.x_range.setPrefix("X Range: ")
        self.x_range.setRange(1, 1000)
        
        self.y_range = QSpinBox()
        self.y_range.setPrefix("Y Range: ")
        self.y_range.setRange(1, 1000)
        
        self.scan_speed = QDoubleSpinBox()
        self.scan_speed.setPrefix("Speed: ")
        self.scan_speed.setRange(0.1, 100.0)
        
        self.scan_button = QPushButton("Start Scan")
        self.scan_button.clicked.connect(self.start_dummy_scan)

        scan_layout.addWidget(self.x_range)
        scan_layout.addWidget(self.y_range)
        scan_layout.addWidget(self.scan_speed)
        scan_layout.addWidget(self.scan_button)
        scan_widget.setLayout(scan_layout)

        scan_dock.setWidget(scan_widget)
        scan_dock.setFeatures(QDockWidget.AllDockWidgetFeatures)
        self.addDockWidget(Qt.TopDockWidgetArea, scan_dock)

    def start_dummy_scan(self):
        print(f"Starting dummy scan: X={self.x_range.value()}, Y={self.y_range.value()}, Speed={self.scan_speed.value()} µm/s")

    def launch_z_regulation_gui(self):
        print("Z-Regulation activated. Connect to backend here.")

    def launch_live_plot(self):
        print("Live plot interface triggered. Will update via pyqtgraph in real-time.")

    def launch_topograph_viewer(self):
        QMessageBox.information(self, "Topograph Viewer", "Topograph viewer activated.")

    def launch_system_diagnostics(self):
        QMessageBox.information(self, "Diagnostics", "System diagnostics initiated.")

    def calibrate_z_scanner(self):
        print("Z-Scanner calibration invoked. Hook into hardware interface.")

    def launch_pattern_matcher(self):
        QMessageBox.information(self, "Pattern Matcher", "Pattern matcher tool opened.")

    def launch_ml_trainer(self):
        QMessageBox.information(self, "ML Trainer", "Machine learning trainer started.")

    def open_documentation(self):
        QMessageBox.information(self, "Documentation", "Opening documentation viewer.")

    def show_about_dialog(self):
        QMessageBox.information(self, "About", "SPM Control Interface v1.0\nDeveloped by Delér Langenberg")
