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
        self.last_command = "initialized"

    def connect(self) -> bool:
        if self.dry_run:
            print(f"[DRY RUN] Connecting to Arduino on {self.port}")
            self.connected = True
            self.last_command = "connect"
            return True

        raise NotImplementedError(
            "Real Arduino connection is intentionally disabled in this safe Phase 5.1 driver."
        )

    def disconnect(self) -> None:
        if self.dry_run:
            print("[DRY RUN] Disconnecting Arduino")
            self.connected = False
            self.serial_conn = None
            self.last_command = "disconnect"
            return

        raise NotImplementedError(
            "Real Arduino disconnect is intentionally disabled in this safe Phase 5.1 driver."
        )

    def move_to(self, z_position: float) -> None:
        if not self.connected:
            raise RuntimeError("Z driver is not connected. Connect first.")

        self.last_z_position = float(z_position)
        self.last_command = "move_to"

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

        current = float(start_z)
        target = float(target_z)

        if current <= target:
            raise ValueError("Approach requires start_z to be greater than target_z.")

        self.last_command = "approach"
        print(f"[DRY RUN] Approach from Z={start_z} to Z={target_z} with step={step}")

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

        current = float(start_z)
        target = float(target_z)

        if current >= target:
            raise ValueError("Retract requires start_z to be less than target_z.")

        self.last_command = "retract"
        print(f"[DRY RUN] Retract from Z={start_z} to Z={target_z} with step={step}")

        while current < target:
            current = min(target, current + step)
            self.last_z_position = current
            print(f"[DRY RUN] Retract step Z={current}")
            time.sleep(0.01)


    def mode_label(self) -> str:
        if self.dry_run:
            return "DRY_RUN"

        return "REAL_SERIAL_DISABLED"

    def is_safe_to_move(self) -> bool:
        return self.connected and self.dry_run

    def get_status(self) -> dict[str, object]:
        return {
            "port": self.port,
            "baudrate": self.baudrate,
            "mode": self.mode_label(),
            "dry_run": self.dry_run,
            "connected": self.connected,
            "serial_open": self.serial_conn is not None,
            "last_z_position": self.last_z_position,
            "last_command": self.last_command,
        }
