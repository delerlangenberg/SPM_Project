from __future__ import annotations

import time
from typing import Dict, Optional, List

from core.motion.motion_backend import MotionBackend

try:
    import serial  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    serial = None


class PrusaGcodeBackend(MotionBackend):
    """
    Motion backend using a Prusa MK4S (or compatible) printer controlled via G-code.

    Safety rule:
    - connect() only opens serial + sets absolute mode (G90). No movement.
    - movement happens only via move_to()/home().
    """

    def __init__(self, *, port: Optional[str] = None, baudrate: int = 115200, timeout: float = 0.5):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self._ser = None
        self._connected = False
        self._last_state: Dict = {"connected": False}

    # -------------------------
    # low-level helpers
    # -------------------------
    def _require_serial(self) -> None:
        if serial is None:
            raise RuntimeError("pyserial is not installed. Run: python -m pip install pyserial")

    def _read_until_ok(self, timeout: float = 3.0) -> List[str]:
        """Collect lines until 'ok' or timeout."""
        assert self._ser is not None
        out: List[str] = []
        end = time.time() + timeout
        while time.time() < end:
            raw = self._ser.readline()
            if not raw:
                continue
            s = raw.decode("utf-8", errors="ignore").strip()
            if not s:
                continue
            out.append(s)
            if s.lower() == "ok" or s.lower().startswith("ok"):
                break
        return out

    def send_gcode(self, cmd: str, *, timeout: float = 3.0) -> List[str]:
        """
        Send a single G-code command and return the response lines (until ok/timeout).
        """
        if not self._connected or self._ser is None:
            raise RuntimeError("Not connected. Call connect() first.")
        line = cmd.strip()
        if not line:
            return []
        self._ser.write((line + "\n").encode("ascii", errors="ignore"))
        self._ser.flush()
        resp = self._read_until_ok(timeout=timeout)
        return resp

    # -------------------------
    # MotionBackend API
    # -------------------------
    def connect(self) -> None:
        """
        Open serial connection and set absolute positioning (G90).
        No movement is performed.
        """
        self._require_serial()
        if not self.port:
            raise ValueError("PrusaGcodeBackend.port is not set (e.g., 'COM5').")

        self._ser = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
        time.sleep(0.8)  # allow printer to settle
        try:
            self._ser.reset_input_buffer()
            self._ser.reset_output_buffer()
        except Exception:
            pass

        self._connected = True
        self._last_state = {"connected": True, "port": self.port, "baudrate": self.baudrate}

        # Safe: absolute mode only, no motion
        try:
            self.send_gcode("G90", timeout=2.0)
        except Exception:
            # Some firmwares may respond differently; don't fail hard here.
            pass

    def disconnect(self) -> None:
        if self._ser is not None:
            try:
                self._ser.close()
            except Exception:
                pass
        self._ser = None
        self._connected = False
        self._last_state = {"connected": False}

    def home(self) -> None:
        # This WILL move the printer. Keep as explicit call.
        self.send_gcode("G28", timeout=30.0)

    def move_to(
        self,
        *,
        x: Optional[float] = None,
        y: Optional[float] = None,
        z: Optional[float] = None,
        feedrate: Optional[float] = None,
    ) -> None:
        # This WILL move the printer. Keep as explicit call.
        parts = ["G1"]
        if x is not None:
            parts.append(f"X{x}")
        if y is not None:
            parts.append(f"Y{y}")
        if z is not None:
            parts.append(f"Z{z}")
        if feedrate is not None:
            parts.append(f"F{feedrate}")
        cmd = " ".join(parts)
        self.send_gcode(cmd, timeout=30.0)

    def get_state(self) -> Dict:
        # Best-effort: return cached info; you can expand to M114 later.
        return dict(self._last_state)

    def emergency_stop(self) -> None:
        # M112 is immediate emergency stop (firmware dependent)
        # This MAY stop heaters/motors. Use carefully.
        try:
            self.send_gcode("M112", timeout=2.0)
        finally:
            self.disconnect()
