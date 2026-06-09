# control/scan_manager.py

import threading
import time

class ScanManager:
    def __init__(self, scan_mode_instance, use_simulation=True):
        """
        Parameters:
            scan_mode_instance (BaseScanMode): Instance of the selected scan mode.
            use_simulation (bool): If True, operate in simulation mode; otherwise, connect to hardware.
        """
        self.scan_mode = scan_mode_instance
        self.use_simulation = use_simulation

        self._scan_thread = None
        self._running = False
        self._paused = False

    def start_scan(self):
        if self._scan_thread and self._scan_thread.is_alive():
            print("Scan already running.")
            return

        self._running = True
        self._paused = False
        self._scan_thread = threading.Thread(target=self._run_scan_loop, daemon=True)
        self._scan_thread.start()
        print("[ScanManager] Scan started.")

    def _run_scan_loop(self):
        while self._running:
            if self._paused:
                time.sleep(0.1)
                continue

            result = self.scan_mode.perform_step()
            if result == "done":
                print("[ScanManager] Scan completed.")
                break

    def pause_scan(self):
        if not self._running:
            print("No scan to pause.")
            return
        self._paused = True
        print("[ScanManager] Scan paused.")

    def resume_scan(self):
        if not self._running:
            print("No scan to resume.")
            return
        self._paused = False
        print("[ScanManager] Scan resumed.")

    def stop_scan(self):
        self._running = False
        self._paused = False
        print("[ScanManager] Scan stopped.")

    def is_running(self):
        return self._running

    def is_paused(self):
        return self._paused
