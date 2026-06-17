# Phase 1.8G Professional Stable Checkpoint

Date: 2026-06-16
Project folder: D:\SPM_Prusa_Project
Branch: main

## Purpose

This checkpoint stabilizes the migrated MK4S-based SPM scanner project after GUI, Z-preview, hardware-status, shutdown-guard, acquisition, hardware-test, and project-structure work.

The old C:\SPM_Project path is no longer active. The only active project path is D:\SPM_Prusa_Project.

## Current milestone status

- GUI syntax validation is required before commit.
- Full pytest validation is required before commit.
- Runtime logs and local backups are intentionally excluded from Git.
- Code, tests, tools, docs, config, data examples, and hardware documentation are staged as milestone artifacts.

## Latest commit before this milestone
```text
2dc1f42 Phase 1 stabilize scanner Z preview and real scan status
```

## Modified tracked files before checkpoint
```text
.gitignore
config/spm_hardware_initialized_profile.json
config/spm_mk4s_config.json
core/application/cli_scan_launcher.py
core/application/gui_scan_launcher.py
core/education/config_loader.py
core/education/safe_raster.py
core/education/scan_profile.py
data/interface_test_output.csv
data/interface_test_output.png
data/safe_raster_5x5_output.csv
data/safe_raster_5x5_output.png
docs/SPM_PROFESSIONAL_PHASE_ROADMAP.md
requirements.txt
tests/test_cli_scan_launcher.py
tests/test_config_loader.py
tests/test_gui_z_dry_run_safety.py
tests/test_safe_raster_module.py
tests/test_scan_profile.py
tools/plot_safe_raster.py
tools/run_configured_raster_scan.py
```

## Untracked files before checkpoint
```text
Hardware/CRTouch_SPM_FINAL_Project.pdf
core/acquisition/__init__.py
core/acquisition/channels.py
core/acquisition/raster_stream.py
core/acquisition/scan_session.py
core/application/hardware_information_cli.py
core/application/hardware_test_console_gui.py
core/application/hardware_test_control_cli.py
core/application/workstation_status.py
core/motion/parking.py
core/system/hardware_diagnostics.py
core/system/hardware_information_exchange.py
core/system/hardware_profile.py
core/system/hardware_test_controls.py
core/system/smart_hardware_assessment.py
core/system/workstation_initializer.py
core/z_control/crtouch_probe_plan.py
data/axis_limit_check_2026_06_11.csv
data/crtouch_spm_final_project_extracted.txt
data/directional_demo_scan_2026_06_11.csv
data/directional_demo_scan_2026_06_11.metadata.json
data/directional_demo_scan_2026_06_11.png
data/educational_spm_clean_flow_dry_test_2026_06_11.csv
data/educational_spm_clean_flow_dry_test_2026_06_11.metadata.json
data/educational_spm_clean_flow_dry_test_2026_06_11.png
data/gui_crash_probe_stderr.txt
data/gui_crash_probe_stdout.txt
data/gui_live_probe_stderr.txt
data/gui_live_probe_stdout.txt
data/hardware_3x3_check_2026_06_11.csv
data/hardware_3x3_check_2026_06_11.metadata.json
data/hardware_3x3_check_2026_06_11.png
data/interface_test_output.metadata.json
data/lightweight_ui_shutdown_gate_dry_test_2026_06_11.csv
data/lightweight_ui_shutdown_gate_dry_test_2026_06_11.metadata.json
data/lightweight_ui_shutdown_gate_dry_test_2026_06_11.png
data/metadata_check.csv
data/metadata_check.metadata.json
data/original_mk4s_max_check_2026_06_11.csv
data/original_mk4s_xy_min_check_2026_06_11.csv
data/overview_progress_check.csv
data/overview_progress_check.png
data/phase1_matrix_workspace_screenshot.png
data/phase1_matrix_workspace_screenshot_clean.png
data/phase7_dry_run_check.csv
data/phase7_dry_run_check.png
data/phase7_preview_check.png
data/phase9_6_dryrun_probe.csv
data/phase9_6_dryrun_probe.metadata.json
data/phase9_6_dryrun_probe.png
data/phase9_x_line_topography_skeleton.csv
data/phase9_x_line_topography_skeleton_v2.csv
data/phase9_x_line_topography_skeleton_v2.png
data/safe_raster_5x5_output.metadata.json
data/stm_demo_mode_dry_test_2026_06_11.csv
data/stm_demo_mode_dry_test_2026_06_11.metadata.json
data/stm_demo_mode_dry_test_2026_06_11.png
data/ui_limit_live_check.csv
data/ui_limit_live_check.metadata.json
data/ui_limit_live_check.png
data/v0.10.1_step1_clear_workstation_windows.png
data/v0.11.1_relaunch_after_crash_fix.png
data/v0.11.2_text_live_scan_stable.png
data/v0.11_auto_measurement_window.png
data/v0.11_live_scan_after_double_click.png
data/v0.11_live_scan_autostart.png
data/v0.11_live_scan_running.png
data/v0.11_main_workspace.png
data/v0.11_measurement_window.png
data/v0.11_measurement_window_after_click.png
data/v0.17.0_hardware_test_console_gui.png
data/v0.18.0_user_friendly_hardware_console.png
data/v0.19.0_guided_hardware_connection_check.png
data/v0.20.0_smart_operator_console.png
data/v0.21.0_main_initialize_z_workflow.png
data/v0.21.0_main_operator_workspace.png
data/v0.21.0_main_operator_workspace_clean.png
data/v0.21.0_main_operator_workspace_final.png
data/v0.21.0_main_operator_workspace_final_clean.png
data/v0.21.0_main_operator_workspace_window.png
data/v0.22.0_essential_z_auto_approach_window.png
data/v0.23.0_single_z_scanner_window.png
data/v0.24.0_connect_approach_measurement_window.png
data/v0.24.0_connect_approach_measurement_window_final.png
data/v0.25.0_focused_main_workflow_window.png
data/v0_11_full_demo_raster.csv
data/v0_11_full_demo_raster.metadata.json
data/v0_11_full_demo_raster.png
data/v0_9_measurement_console_demo_2026_06_11.csv
data/v0_9_measurement_console_demo_2026_06_11.metadata.json
data/v0_9_measurement_console_demo_2026_06_11.png
docs/ACADEMIC_AI_API_INTEGRATION_PLAN_2026-06-12.md
docs/CRTOUCH_SPM_Z_SCANNER_PHASE_PLAN_2026-06-12.md
docs/MK4S_MACHINE_LIMITS_AND_HARDWARE_TEST_2026-06-11.md
docs/PHASE1_CODE_MAP.md
docs/PHASE1_CODE_ONLY_MAP.md
docs/PHASE1_Z_CLIPBOARD_REPORT.txt
docs/PHASE1_Z_GUI_FUNCTIONS.md
docs/PHASE1_Z_INVESTIGATION_SMALL.md
docs/PHASE_1_8F_DIRTY_TREE_CLASSIFICATION_2026-06-16.md
docs/PHASE_7_REPAIR_STATUS_2026-06-10.md
docs/PHASE_9_6_ROBUST_EXECUTOR_ROADMAP_2026-06-12.md
docs/SPM_MODE_WORKFLOW_NOTES_2026-06-11.md
docs/TWO_LAYER_SPM_DEVELOPMENT_ROADMAP_2026-06-12.md
docs/versions/v0.10.0_matrix_workspace_phase1_2026-06-11/README.md
docs/versions/v0.10.0_matrix_workspace_phase1_2026-06-11/backup/gui_scan_launcher.py
docs/versions/v0.10.0_matrix_workspace_phase1_2026-06-11/backup/test_gui_z_dry_run_safety.py
docs/versions/v0.10.1_clear_workstation_windows_2026-06-11/README.md
docs/versions/v0.10.1_clear_workstation_windows_2026-06-11/backup/gui_scan_launcher.py
docs/versions/v0.10.1_clear_workstation_windows_2026-06-11/backup/test_gui_z_dry_run_safety.py
docs/versions/v0.11.0_live_spm_raster_measurement_2026-06-11/README.md
docs/versions/v0.11.0_live_spm_raster_measurement_2026-06-11/backup/gui_scan_launcher.py
docs/versions/v0.11.0_live_spm_raster_measurement_2026-06-11/backup/test_gui_z_dry_run_safety.py
docs/versions/v0.11.1_crash_hardened_live_measurement_2026-06-11/README.md
docs/versions/v0.11.1_crash_hardened_live_measurement_2026-06-11/backup/gui_scan_launcher.py
docs/versions/v0.11.1_crash_hardened_live_measurement_2026-06-11/backup/test_gui_z_dry_run_safety.py
docs/versions/v0.11.2_text_live_scan_stability_2026-06-11/README.md
docs/versions/v0.11.2_text_live_scan_stability_2026-06-11/backup/gui_scan_launcher.py
docs/versions/v0.11.2_text_live_scan_stability_2026-06-11/backup/test_gui_z_dry_run_safety.py
docs/versions/v0.14.0_phase9_6_robust_executor_2026-06-12/README.md
docs/versions/v0.14.0_phase9_6_robust_executor_2026-06-12/backup/PHASE_9_6_ROBUST_EXECUTOR_ROADMAP_2026-06-12.md
docs/versions/v0.14.0_phase9_6_robust_executor_2026-06-12/backup/README.md
docs/versions/v0.14.0_phase9_6_robust_executor_2026-06-12/backup/phase9_xy_10x10_topography_skeleton.py
docs/versions/v0.15.0_hardware_information_layer_and_crtouch_plan_2026-06-12/README.md
docs/versions/v0.15.0_hardware_information_layer_and_crtouch_plan_2026-06-12/backup/ACADEMIC_AI_API_INTEGRATION_PLAN_2026-06-12.md
docs/versions/v0.15.0_hardware_information_layer_and_crtouch_plan_2026-06-12/backup/CRTOUCH_SPM_Z_SCANNER_PHASE_PLAN_2026-06-12.md
docs/versions/v0.15.0_hardware_information_layer_and_crtouch_plan_2026-06-12/backup/README.md
docs/versions/v0.15.0_hardware_information_layer_and_crtouch_plan_2026-06-12/backup/TWO_LAYER_SPM_DEVELOPMENT_ROADMAP_2026-06-12.md
docs/versions/v0.15.0_hardware_information_layer_and_crtouch_plan_2026-06-12/backup/crtouch_probe_plan.py
docs/versions/v0.15.0_hardware_information_layer_and_crtouch_plan_2026-06-12/backup/hardware_information_cli.py
docs/versions/v0.15.0_hardware_information_layer_and_crtouch_plan_2026-06-12/backup/hardware_information_exchange.py
docs/versions/v0.15.0_hardware_information_layer_and_crtouch_plan_2026-06-12/backup/test_crtouch_probe_plan.py
docs/versions/v0.15.0_hardware_information_layer_and_crtouch_plan_2026-06-12/backup/test_hardware_information_exchange.py
docs/versions/v0.16.0_ht3_hardware_test_controls_2026-06-12/README.md
docs/versions/v0.16.0_ht3_hardware_test_controls_2026-06-12/backup/README.md
docs/versions/v0.16.0_ht3_hardware_test_controls_2026-06-12/backup/TWO_LAYER_SPM_DEVELOPMENT_ROADMAP_2026-06-12.md
docs/versions/v0.16.0_ht3_hardware_test_controls_2026-06-12/backup/hardware_test_control_cli.py
docs/versions/v0.16.0_ht3_hardware_test_controls_2026-06-12/backup/hardware_test_controls.py
docs/versions/v0.16.0_ht3_hardware_test_controls_2026-06-12/backup/test_hardware_test_controls.py
docs/versions/v0.17.0_ht3_1_hardware_test_console_gui_2026-06-12/README.md
docs/versions/v0.17.0_ht3_1_hardware_test_console_gui_2026-06-12/backup/README.md
docs/versions/v0.17.0_ht3_1_hardware_test_console_gui_2026-06-12/backup/TWO_LAYER_SPM_DEVELOPMENT_ROADMAP_2026-06-12.md
docs/versions/v0.17.0_ht3_1_hardware_test_console_gui_2026-06-12/backup/hardware_test_console_gui.py
docs/versions/v0.17.0_ht3_1_hardware_test_console_gui_2026-06-12/backup/test_hardware_test_console_gui.py
docs/versions/v0.18.0_ht3_2_user_friendly_hardware_console_2026-06-12/README.md
docs/versions/v0.18.0_ht3_2_user_friendly_hardware_console_2026-06-12/TWO_LAYER_SPM_DEVELOPMENT_ROADMAP_2026-06-12.md
docs/versions/v0.18.0_ht3_2_user_friendly_hardware_console_2026-06-12/hardware_test_console_gui.py
docs/versions/v0.18.0_ht3_2_user_friendly_hardware_console_2026-06-12/test_hardware_test_console_gui.py
docs/versions/v0.19.0_ht3_3_guided_hardware_connection_check_2026-06-12/README.md
docs/versions/v0.19.0_ht3_3_guided_hardware_connection_check_2026-06-12/TWO_LAYER_SPM_DEVELOPMENT_ROADMAP_2026-06-12.md
docs/versions/v0.19.0_ht3_3_guided_hardware_connection_check_2026-06-12/hardware_test_console_gui.py
docs/versions/v0.19.0_ht3_3_guided_hardware_connection_check_2026-06-12/test_hardware_test_console_gui.py
docs/versions/v0.20.0_ht3_4_smart_operator_console_2026-06-12/README.md
docs/versions/v0.20.0_ht3_4_smart_operator_console_2026-06-12/TWO_LAYER_SPM_DEVELOPMENT_ROADMAP_2026-06-12.md
docs/versions/v0.20.0_ht3_4_smart_operator_console_2026-06-12/hardware_test_console_gui.py
docs/versions/v0.20.0_ht3_4_smart_operator_console_2026-06-12/smart_hardware_assessment.py
docs/versions/v0.20.0_ht3_4_smart_operator_console_2026-06-12/test_hardware_test_console_gui.py
docs/versions/v0.20.0_ht3_4_smart_operator_console_2026-06-12/test_smart_hardware_assessment.py
docs/versions/v0.21.0_main_initialize_and_z_scanner_workflow_2026-06-12/README.md
docs/versions/v0.21.0_main_initialize_and_z_scanner_workflow_2026-06-12/TWO_LAYER_SPM_DEVELOPMENT_ROADMAP_2026-06-12.md
docs/versions/v0.21.0_main_initialize_and_z_scanner_workflow_2026-06-12/gui_scan_launcher.py
docs/versions/v0.21.0_main_initialize_and_z_scanner_workflow_2026-06-12/test_gui_z_dry_run_safety.py
docs/versions/v0.21.0_main_initialize_and_z_scanner_workflow_2026-06-12/test_workstation_initializer.py
docs/versions/v0.21.0_main_initialize_and_z_scanner_workflow_2026-06-12/workstation_initializer.py
docs/versions/v0.22.0_essential_initialize_and_mk4s_z_auto_approach_2026-06-12/README.md
docs/versions/v0.22.0_essential_initialize_and_mk4s_z_auto_approach_2026-06-12/TWO_LAYER_SPM_DEVELOPMENT_ROADMAP_2026-06-12.md
docs/versions/v0.22.0_essential_initialize_and_mk4s_z_auto_approach_2026-06-12/gui_scan_launcher.py
docs/versions/v0.22.0_essential_initialize_and_mk4s_z_auto_approach_2026-06-12/mk4s_z_auto_approach.py
docs/versions/v0.22.0_essential_initialize_and_mk4s_z_auto_approach_2026-06-12/test_gui_z_dry_run_safety.py
docs/versions/v0.22.0_essential_initialize_and_mk4s_z_auto_approach_2026-06-12/test_mk4s_z_auto_approach.py
docs/versions/v0.23.0_single_z_scanner_gwyddion_cleanup_2026-06-12/README.md
docs/versions/v0.23.0_single_z_scanner_gwyddion_cleanup_2026-06-12/TWO_LAYER_SPM_DEVELOPMENT_ROADMAP_2026-06-12.md
docs/versions/v0.23.0_single_z_scanner_gwyddion_cleanup_2026-06-12/gui_scan_launcher.py
docs/versions/v0.23.0_single_z_scanner_gwyddion_cleanup_2026-06-12/test_gui_z_dry_run_safety.py
docs/versions/v0.24.0_connect_approach_measurement_main_page_2026-06-12/README.md
docs/versions/v0.24.0_connect_approach_measurement_main_page_2026-06-12/TWO_LAYER_SPM_DEVELOPMENT_ROADMAP_2026-06-12.md
docs/versions/v0.24.0_connect_approach_measurement_main_page_2026-06-12/gui_scan_launcher.py
docs/versions/v0.24.0_connect_approach_measurement_main_page_2026-06-12/mk4s_z_auto_approach.py
docs/versions/v0.24.0_connect_approach_measurement_main_page_2026-06-12/test_gui_z_dry_run_safety.py
docs/versions/v0.24.0_connect_approach_measurement_main_page_2026-06-12/test_mk4s_z_auto_approach.py
docs/versions/v0.25.0_focused_main_workflow_cleanup_2026-06-15/README.md
docs/versions/v0.25.0_focused_main_workflow_cleanup_2026-06-15/TWO_LAYER_SPM_DEVELOPMENT_ROADMAP_2026-06-12.md
docs/versions/v0.25.0_focused_main_workflow_cleanup_2026-06-15/gui_scan_launcher.py
docs/versions/v0.25.0_focused_main_workflow_cleanup_2026-06-15/test_gui_z_dry_run_safety.py
docs/versions/v0.25.0_focused_main_workflow_cleanup_2026-06-15/v0.25.0_focused_main_workflow_window.png
docs/versions/v0.9.0_measurement_console_2026-06-11/README.md
docs/versions/v0.9.0_measurement_console_2026-06-11/backup/gui_scan_launcher.py
docs/versions/v0.9.0_measurement_console_2026-06-11/backup/raster_stream.py
docs/versions/v0.9.0_measurement_console_2026-06-11/backup/run_configured_raster_scan.py
docs/versions/v0.9.0_measurement_console_2026-06-11/backup/safe_raster.py
docs/versions/v0.9.0_measurement_console_2026-06-11/backup/workstation_status.py
tests/test_acquisition_channels.py
tests/test_auto_step_z_approach_reference.py
tests/test_axis_direction_observation.py
tests/test_crtouch_probe_plan.py
tests/test_gui_append_log_shutdown_guard.py
tests/test_gui_status_refresh_shutdown_guard.py
tests/test_hardware_diagnostics.py
tests/test_hardware_information_exchange.py
tests/test_hardware_motion_limits_profile.py
tests/test_hardware_profile.py
tests/test_hardware_test_console_gui.py
tests/test_hardware_test_controls.py
tests/test_mk4s_z_auto_approach.py
tests/test_parking.py
tests/test_plot_safe_raster_cli.py
tests/test_raster_stream.py
tests/test_scan_session.py
tests/test_smart_hardware_assessment.py
tests/test_workstation_initializer.py
tests/test_workstation_status.py
tests/test_y_axis_direction_observation.py
tests/test_z_axis_direction_observation.py
tools/park_mk4s.py
tools/phase8_read_machine_limits.py
tools/phase8_x_max_limit_test.py
tools/phase8_x_visible_move_5mm.py
tools/phase8_xyz_readonly_status.py
tools/phase8_y_max_limit_test.py
tools/phase8_y_visible_move_5mm.py
tools/phase8_z_safe_visible_move.py
tools/phase9_auto_step_z_approach_foam.py
tools/phase9_auto_z_probe_foam.py
tools/phase9_center_alignment_only.py
tools/phase9_manual_z_approach_foam.py
tools/phase9_manual_z_approach_foam_center.py
tools/phase9_retract_from_foam.py
tools/phase9_x_line_topography_skeleton.py
tools/phase9_x_line_topography_skeleton_v2.py
tools/phase9_xy_10x10_topography_skeleton.py
tools/phase9_xy_3x3_topography_skeleton.py
tools/query_mk4s_machine_limits.py
tools/run_axis_limit_check.py
```

## Next development direction after this checkpoint

1. Keep this checkpoint as the stable restart point.
2. Continue with a focused operator workflow: connect hardware, initialize Z, preview scan, run real scan, export Gwyddion-compatible data.
3. Avoid large GUI rewrites until the main workflow is stable.
4. Future work should be done in small tested phases from this checkpoint.

