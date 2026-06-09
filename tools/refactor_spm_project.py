# refactor_spm_project.py
import os
import shutil
import re

PROJECT_ROOT = r"D:\Documents\Project\SPM"  # Update if your root differs

# Mapping of source files to their new locations
MOVE_MAP = {
    # Simulation files
    os.path.join(PROJECT_ROOT, "core", "z_control", "z_simulator.py"): os.path.join(PROJECT_ROOT, "simulation", "z_simulator.py"),
    os.path.join(PROJECT_ROOT, "core", "scan", "scan_simulator.py"): os.path.join(PROJECT_ROOT, "simulation", "scan_simulation.py"),  # rename here
    # core/scan splitting - adjust filenames as per your actual files
    os.path.join(PROJECT_ROOT, "core", "scan", "stm_mode.py"): os.path.join(PROJECT_ROOT, "core", "scan", "modes", "stm_mode.py"),
    os.path.join(PROJECT_ROOT, "core", "scan", "profiling_mode.py"): os.path.join(PROJECT_ROOT, "core", "scan", "modes", "profiling_mode.py"),
    os.path.join(PROJECT_ROOT, "core", "scan", "afm_contact_mode.py"): os.path.join(PROJECT_ROOT, "core", "scan", "modes", "afm_contact_mode.py"),
    os.path.join(PROJECT_ROOT, "core", "scan", "afm_noncontact_mode.py"): os.path.join(PROJECT_ROOT, "core", "scan", "modes", "afm_noncontact_mode.py"),
    os.path.join(PROJECT_ROOT, "core", "scan", "scan_controller.py"): os.path.join(PROJECT_ROOT, "core", "scan", "controller", "scan_controller.py"),
    os.path.join(PROJECT_ROOT, "core", "scan", "scan_manager.py"): os.path.join(PROJECT_ROOT, "core", "scan", "controller", "scan_manager.py"),
    os.path.join(PROJECT_ROOT, "core", "scan", "spm_workflow.py"): os.path.join(PROJECT_ROOT, "core", "scan", "workflow", "spm_workflow.py"),
}

# Scripts to move from root to utils/validation/
ROOT_SCRIPTS_TO_MOVE = [
    "fix_missing_launch_functions.py",
    "validate_launch_functions.py",
    "validate_and_fix_launch_functions.py",
]

IMPORT_REPLACEMENTS = {
    # old import : new import
    "simulation.z_simulator": "simulation.z_simulator",
    "simulation.scan_simulation": "simulation.scan_simulation",
    "core.scan.modes.stm_mode": "core.scan.modes.stm_mode",
    "core.scan.modes.profiling_mode": "core.scan.modes.profiling_mode",
    "core.scan.modes.afm_contact_mode": "core.scan.modes.afm_contact_mode",
    "core.scan.modes.afm_noncontact_mode": "core.scan.modes.afm_noncontact_mode",
    "core.scan.controller.scan_controller": "core.scan.controller.scan_controller",
    "core.scan.controller.scan_manager": "core.scan.controller.scan_manager",
    "core.scan.workflow.spm_workflow": "core.scan.workflow.spm_workflow",
}

def ensure_dir_exists(path):
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"Created directory: {path}")

def move_files():
    print("Moving files according to MOVE_MAP...")
    for src, dst in MOVE_MAP.items():
        if not os.path.exists(src):
            print(f"Source file does not exist, skipping: {src}")
            continue
        dst_dir = os.path.dirname(dst)
        ensure_dir_exists(dst_dir)
        if os.path.exists(dst):
            print(f"Destination file already exists (backup not implemented): {dst}")
            # Optionally backup old dst here if you want
            continue
        shutil.move(src, dst)
        print(f"Moved {src} -> {dst}")

def move_root_scripts():
    utils_validation_dir = os.path.join(PROJECT_ROOT, "utils", "validation")
    ensure_dir_exists(utils_validation_dir)
    for script in ROOT_SCRIPTS_TO_MOVE:
        src = os.path.join(PROJECT_ROOT, script)
        dst = os.path.join(utils_validation_dir, script)
        if not os.path.exists(src):
            print(f"Root script not found, skipping: {script}")
            continue
        if os.path.exists(dst):
            print(f"Destination script already exists, skipping move: {dst}")
            continue
        shutil.move(src, dst)
        print(f"Moved root script {script} -> utils/validation/")

def update_imports():
    print("Updating import statements across project...")
    pattern = re.compile(r'(^|\s)(from|import)\s+([a-zA-Z0-9_.]+)')
    for root, _, files in os.walk(PROJECT_ROOT):
        for file in files:
            if file.endswith(".py"):
                path = os.path.join(root, file)
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()

                original_content = content

                for old_import, new_import in IMPORT_REPLACEMENTS.items():
                    # Replace import statements:
                    # from simulation.z_simulator import ...
                    # import simulation.z_simulator
                    content = re.sub(rf'\b{re.escape(old_import)}\b', new_import, content)

                if content != original_content:
                    with open(path, "w", encoding="utf-8") as f:
                        f.write(content)
                    print(f"Updated imports in {path}")

def main():
    print("Starting refactor script for SPM project...")
    move_files()
    move_root_scripts()
    update_imports()
    print("Refactor complete. Please verify manually and run tests.")

if __name__ == "__main__":
    main()
