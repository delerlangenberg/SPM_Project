import os

# Directory where tests should be saved
base_dir = "D:/Documents/Project/SPM/tests"

# Ensure tests folder exists
os.makedirs(base_dir, exist_ok=True)

# Module mapping
test_files = {
    "test_stm_mode.py": "core.scan.modes.stm_mode",
    "test_profiling_mode.py": "core.scan.modes.profiling_mode",
    "test_afm_contact_mode.py": "core.scan.modes.afm_contact_mode",
    "test_afm_noncontact_mode.py": "core.scan.modes.afm_noncontact_mode",
    "test_z_driver_arduino.py": "hardware.z_control.z_driver_arduino",
    "test_z_driver_simulated.py": "simulation.z_simulator",
    "test_z_feedback.py": "core.z_control.z_feedback",
    "test_z_interface.py": "core.z_control.z_interface",
    "test_z_plotter.py": "core.z_control.z_plotter",
    "test_hardware_controls.py": "hardware.motor.motor_controller",
    "test_live_plot_area.py": "visualization.live_plot_area",
    "test_main_window.py": "interface.layout.main_window",
    "test_menu_bar.py": "interface.layout.menu_bar",
    "test_scanning_panel.py": "interface.panels.scanning_panel",
    "test_scan_control_panel.py": "interface.panels.scan_control_panel",
    "test_status_bar.py": "interface.layout.status_bar",
    "test_system_diagnostics.py": "core.system.system_diagnostics",
    "test_z_regulation_gui.py": "interface.panels.z_regulation_gui",
    "test_ai_utils.py": "ai.utils.ai_utils",
    "test_ml_model.py": "ai.models.ml_model",
    "test_pattern_matcher.py": "processing.pattern_matching.pattern_matcher",
}

# Generator
def generate_test_content(module_path):
    module_name = module_path.split('.')[-1]
    class_name = "Test" + ''.join(word.capitalize() for word in module_name.split('_'))
    return f"""import pytest
import {module_path} as mod

class {class_name}:
    def test_placeholder(self):
        pass
"""

# Write all test files
for filename, module_path in test_files.items():
    filepath = os.path.join(base_dir, filename)
    with open(filepath, "w") as f:
        f.write(generate_test_content(module_path))

print("✅ Test stubs created.")
