# File: core/z_control/z_driver_arduino_safe.py

from __future__ import annotations

import time


class ZDriverArduino:
    """
    Safe Arduino Z-control driver for Phase 5.1.

    Default mode is dry_run=True.
    In dry-run mode, no real serial connection is opened and no hardware moves.
    """

    def __init__(self, port: str = "COM5", baudrate: int = 115200, dry_run: bool = True):
        self.port = port
        self.baudrate = baudrate
        self.dry_run = dry_run
        self.serial_conn = None
        self.connected = False
        self.last_z_position = None

    def connect(self) -> bool:
        if self.dry_run:
            print(f"[DRY RUN] Connecting to Arduino on {self.port}")
            self.connected = True
            return True

        raise NotImplementedError(
            "Real Arduino connection is intentionally disabled in this safe Phase 5.1 driver."
        )

    def disconnect(self) -> None:
        if self.dry_run:
            print("[DRY RUN] Disconnecting Arduino")
            self.connected = False
            self.serial_conn = None
            return

        raise NotImplementedError(
            "Real Arduino disconnect is intentionally disabled in this safe Phase 5.1 driver."
        )

    def move_to(self, z_position: float) -> None:
        if not self.connected:
            raise RuntimeError("Z driver is not connected. Connect first.")

        self.last_z_position = float(z_position)

        if self.dry_run:
            print(f"[DRY RUN] Move to Z={self.last_z_position}")
            return

        raise NotImplementedError(
            "Real Z movement is intentionally disabled in this safe Phase 5.1 driver."
        )

    def approach(self, start_z: float, target_z: float, step: float = 1.0) -> None:
        if not self.connected:
            raise RuntimeError("Z driver is not connected. Connect first.")

        if step <= 0:
            raise ValueError("Approach step must be positive.")

        print(f"[DRY RUN] Approach from Z={start_z} to Z={target_z} with step={step}")

        current = float(start_z)
        target = float(target_z)

        while current > target:
            current = max(target, current - step)
            self.last_z_position = current
            print(f"[DRY RUN] Approach step Z={current}")
            time.sleep(0.01)

    def retract(self, start_z: float, target_z: float, step: float = 1.0) -> None:
        if not self.connected:
            raise RuntimeError("Z driver is not connected. Connect first.")

        if step <= 0:
            raise ValueError("Retract step must be positive.")

        print(f"[DRY RUN] Retract from Z={start_z} to Z={target_z} with step={step}")

        current = float(start_z)
        target = float(target_z)

        while current < target:
            current = min(target, current + step)
            self.last_z_position = current
            print(f"[DRY RUN] Retract step Z={current}")
            time.sleep(0.01)
