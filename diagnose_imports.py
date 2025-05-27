import importlib

modules = [
    "core.scan.modes.afm_noncontact_mode",
    "ai.utils.ai_utils",
    "hardware.motor.motor_controller",
    "visualization.live_plot_area",
    "interface.layout.main_window",
    "interface.layout.menu_bar",
    "ai.models.ml_model",
    "processing.pattern_matching.pattern_matcher",
    "interface.panels.scan_control_panel",
    "interface.panels.scanning_panel",
    "core.system.system_diagnostics",
    "hardware.z_control.z_driver_arduino",
    "simulation.z_simulator",
    "interface.panels.z_regulation_gui"
]

for m in modules:
    try:
        importlib.import_module(m)
        print(f"✅ {m}")
    except Exception as e:
        print(f"❌ {m}: {type(e).__name__}: {e}")
