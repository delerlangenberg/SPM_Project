import importlib

# Map of modules and expected function names
launch_targets = {
    'interface.layout.live_plot_area': 'launch_live_plot',
    'interface.layout.z_regulation_gui': 'launch_z_gui',
    'interface.layout.scan_control_panel': 'launch_scan_control',
    'interface.layout.scanning_panel': 'launch_scanning_panel',
    'interface.layout.hardware_controls': 'launch_hardware_controls',
    'interface.layout.system_diagnostics': 'launch_diagnostics',
}

# Loop over and validate
for module_path, function_name in launch_targets.items():
    try:
        mod = importlib.import_module(module_path)
        if not hasattr(mod, function_name):
            print(f"❌ Missing: {function_name}() in {module_path}")
        else:
            print(f"✅ Found: {function_name}() in {module_path}")
    except ModuleNotFoundError as e:
        print(f"🚫 Could not import module: {module_path}")
    except Exception as e:
        print(f"⚠️ Error in {module_path}: {e}")
