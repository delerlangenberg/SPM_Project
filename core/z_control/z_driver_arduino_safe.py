# File: core/z_control/z_driver_arduino_safe.py

import serial
import time

class ZDriverArduino:
    """
    Safe Arduino Z-control driver for Phase 5 integration.
    Provides approach/retract without altering GUI code.
    """

    def __init__(self, port="COM5", baudrate=115200, dry_run=True):
        self.port = port
        self.baudrate = baudrate
        self.dry_run = dry_run
        self.serial_conn = None

    def connect(self):
        if self.dry_run:
            print(f"[DRY RUN] Connecting to Arduino on {self.port}")
            return True
        try:
            self.serial_conn = serial.Serial(self.port, self.baudrate, timeout=1)
            time.sleep(2)
            print(f"Connected to Arduino on {self.port}")
            return True
        except Exception as e:
            print(f"Failed to connect to Arduino: {e}")
            return False

    def disconnect(self):
        if self.dry_run:
            print("[DRY RUN] Disconnecting Arduino")
            return
        if self.serial_conn:
            self.serial_conn.close()
            self.serial_conn = None
            print("Arduino disconnected")

    def move_to(self, z_position):
        if self.dry_run:
            print(f"[DRY RUN] Move to Z={z_position}")
            return
        cmd = f"G0 Z{z_position}\n".encode()
        self.serial_conn.write(cmd)
        print(f"Sent command: {cmd.decode().strip()}")
