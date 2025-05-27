import importlib
import os
import sys
import inspect
import shutil
from datetime import datetime

# Project root - must be set correctly before running
PROJECT_ROOT = r"D:\Documents\Project\SPM"  # <-- Adjust if needed

# Map modules to functions expected
MODULE_FUNCTION_MAP = {
    "hardware.adc_interface": ["test_adc"],
    "core.scan.modes.afm_contact_mode": ["run_contact_scan"],
    "core.scan.modes.afm_noncontact_mode": ["run_noncontact_scan"],
    "hardware.arduino_link": ["setup_arduino"],
    "interface.layout.hardware_controls": ["launch_hardware_controls"],
    "processing.image_tools": ["launch_tools"],
    "interface.layout.live_plot_area": ["launch_live_plot"],
    "ai.ml_model": ["run_model"],
    "ai.pattern_matcher": ["match_patterns"],
    "visualization.plot": ["render_plot"],
    "processing.process_pipeline": ["run_pipeline"],
    "interface.layout.scan_control_panel": ["launch_scan_control"],
    "interface.layout.scanning_panel": ["launch_scanning_panel"],
    "core.scan.modes.stm_mode": ["run_stm_scan"],
    "interface.layout.system_diagnostics": ["launch_diagnostics"],
    "visualization.topograph": ["render_topograph"],
    "visualization.viewer": ["launch_viewer"],
    "core.z_control.z_feedback": ["run_feedback_loop"],
    "core.z_control.z_interface": ["launch_z_interface"],
    "core.z_control.z_plotter": ["launch_z_plotter"],
    "interface.layout.z_regulation_gui": ["launch_z_gui"],
    "hardware.z_scanner_driver": ["run_driver"],
}

# Terminal color codes for output clarity
class TermColors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    RESET = '\033[0m'

def log(message, color=None):
    if color:
        print(f"{color}{message}{TermColors.RESET}")
    else:
        print(message)

def backup_file(file_path):
    if not os.path.isfile(file_path):
        return
    backup_path = file_path + f".bak_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(file_path, backup_path)
    log(f"Backup created: {backup_path}", TermColors.YELLOW)

def add_stub_function_to_file(file_path, function_name):
    # Backup before writing!
    backup_file(file_path)

    stub_code = f"""

def {function_name}():
    \"\"\"Stub implementation of {function_name} in {os.path.basename(file_path)}.
    TODO: Replace with actual implementation.\"\"\"
    import logging
    logging.warning("Stub function '{function_name}' called. Please implement properly.")
    # TODO: Implement {function_name}
"""

    with open(file_path, "a", encoding="utf-8") as f:
        f.write(stub_code)

def validate_and_fix():
    # Ensure PROJECT_ROOT is in sys.path for imports
    if PROJECT_ROOT not in sys.path:
        sys.path.insert(0, PROJECT_ROOT)

    for module_name, func_list in MODULE_FUNCTION_MAP.items():
        try:
            mod = importlib.import_module(module_name)
        except ModuleNotFoundError:
            log(f"❌ Module not found: {module_name}", TermColors.RED)
            continue
        except Exception as e:
            log(f"❌ Unexpected error importing {module_name}: {e}", TermColors.RED)
            continue

        # Locate file for module
        try:
            file_path = inspect.getfile(mod)
        except TypeError:
            log(f"❌ Cannot locate source file for module {module_name}", TermColors.RED)
            continue

        for func_name in func_list:
            if hasattr(mod, func_name) and callable(getattr(mod, func_name)):
                log(f"✅ Function {func_name} found in {module_name}", TermColors.GREEN)
            else:
                log(f"❌ Function {func_name} missing in {module_name} - Adding stub", TermColors.RED)
                add_stub_function_to_file(file_path, func_name)

if __name__ == "__main__":
    validate_and_fix()
