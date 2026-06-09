"""
File: D:\Documents\Project\SPM_Reorganized\control\spm_workflow.py

Description: Implements structured execution workflows for complete SPM operations.
Supports automated scanning sequences, adaptive feedback control, and multi-step data processing.
"""

import logging
from control.scan_control import ScanControl
from analysis.spectroscopy_engine import SpectroscopyEngine
from processing.real_time_processing import RealTimeProcessing

class SPMWorkflow:
    """Manages structured SPM execution workflow, ensuring systematic operation."""

    def __init__(self, scan_control, spectroscopy_engine, processing_engine):
        """
        Initializes the SPM workflow manager.

        :param scan_control: Handles scan execution.
        :param spectroscopy_engine: Manages spectroscopy data acquisition.
        :param processing_engine: Enables real-time signal analysis.
        """
        self.scan_control = scan_control
        self.spectroscopy_engine = spectroscopy_engine
        self.processing_engine = processing_engine
        logging.info("SPM Workflow Manager Initialized.")

    def execute_full_scan(self, mode, scan_speed, resolution):
        """
        Runs a complete scan workflow from initialization to data processing.

        :param mode: Scanning mode (`STM`, `AFM_contact`, `AFM_noncontact`).
        :param scan_speed: Desired speed for scanning.
        :param resolution: Resolution of the scan.
        """
        logging.info(f"Executing full {mode} scan workflow...")

        # Step 1: Start scan execution
        self.scan_control.start_scan(0, resolution, scan_speed)

        # Step 2: Acquire spectroscopy data
        spectroscopy_data = self.spectroscopy_engine.acquire_spectrum(mode)
        logging.info("Spectroscopy data collected.")

        # Step 3: Process scan data in real-time
        processed_data = self.processing_engine.adaptive_filter(spectroscopy_data["values"])
        logging.info("Signal processing completed.")

        logging.info("Full SPM workflow execution completed.")

# Usage in Main Application
if __name__ == "__main__":
    from hardware.hardware_controller import HardwareController

    controller = HardwareController()
    scan_control = ScanControl(controller, None)
    spectroscopy_engine = SpectroscopyEngine()
    processing_engine = RealTimeProcessing()

    workflow_manager = SPMWorkflow(scan_control, spectroscopy_engine, processing_engine)
    workflow_manager.execute_full_scan("STM", 70, 1024)
