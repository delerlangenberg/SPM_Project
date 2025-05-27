import logging
import os
import sys
import time

class SystemRecovery:
    """Automated system recovery handler for detecting and responding to critical failures."""
    
    def __init__(self, restart_attempts=3):
        self.restart_attempts = restart_attempts
        logging.info("Initializing Automated System Recovery Engine...")

    def check_system_status(self):
        """Performs a basic health check on essential components."""
        required_paths = [
            "D:/Documents/Project/SPM_Reorganized/main.py",
            "D:/Documents/Project/SPM_Reorganized/gui/main_window.py",
            "D:/Documents/Project/SPM_Reorganized/control/scan_execution.py",
            "D:/Documents/Project/SPM_Reorganized/analysis/spectroscopy_engine.py"
        ]
        
        missing_files = [path for path in required_paths if not os.path.exists(path)]
        
        if missing_files:
            logging.warning(f"⚠ Critical files missing: {missing_files}")
            return False
        logging.info("✅ All critical system components are present.")
        return True

    def restart_system(self):
        """Attempts to restart the system in case of failure."""
        for attempt in range(1, self.restart_attempts + 1):
            logging.info(f"🔄 Attempting system restart ({attempt}/{self.restart_attempts})...")
            os.system(f"python D:/Documents/Project/SPM_Reorganized/main.py")
            time.sleep(2)  # Allow startup time
            
            if self.check_system_status():
                logging.info("✅ System successfully restarted.")
                return
        logging.error("❌ Failed to restart the system after multiple attempts.")

# Example Usage:
if __name__ == "__main__":
    recovery = SystemRecovery()
    if not recovery.check_system_status():
        recovery.restart_system()