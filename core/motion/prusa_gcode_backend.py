from __future__ import annotations

import re
import time
from typing import Dict, Optional, List, Tuple

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

    def __init__(
        self,
        *,
        port: Optional[str] = None,
        baudrate: int = 115200,
        timeout: float = 0.5,
        auto_detect_port: bool = True,
        x_limits: Optional[Tuple[float, float]] = None,
        y_limits: Optional[Tuple[float, float]] = None,
        z_limits: Optional[Tuple[float, float]] = None,
    ):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.auto_detect_port = auto_detect_port
        self.x_limits = x_limits
        self.y_limits = y_limits
        self.z_limits = z_limits
        self._ser = None
        self._connected = False
        self._last_position: Dict[str, float] = {}
        self._last_state: Dict = {"connected": False, "position": {}}

    # -------------------------
    # low-level helpers
    # -------------------------
    def _require_serial(self) -> None:
        if serial is None:
            raise RuntimeError("pyserial is not installed. Run: python -m pip install pyserial")

    def _auto_detect_prusa_port(self) -> Optional[str]:
        """
        Best-effort serial port discovery for Prusa/USB CDC devices.
        """
        if serial is None:
            return None
        try:
            from serial.tools import list_ports  # type: ignore
        except Exception:
            return None

        ports = list(list_ports.comports())
        if not ports:
            return None

        # Prefer ports that look like Prusa USB serial endpoints.
        for p in ports:
            blob = f"{getattr(p, 'device', '')} {getattr(p, 'description', '')} {getattr(p, 'manufacturer', '')}".lower()
            if "prusa" in blob:
                return p.device

        # Fallbacks that work on Linux/macOS/Windows for USB serial printers.
        for p in ports:
            dev = str(getattr(p, "device", ""))
            if any(s in dev for s in ("/dev/ttyACM", "/dev/ttyUSB", "/dev/cu.usb", "COM")):
                return dev

        return ports[0].device

    def _parse_m114(self, lines: List[str]) -> Dict[str, float]:
        """
        Parse M114 response lines into position dict.
        Expected tokens include X:.. Y:.. Z:.. (E optional).
        """
        joined = " ".join(lines)
        out: Dict[str, float] = {}
        for axis in ("X", "Y", "Z", "E"):
            m = re.search(rf"\b{axis}:\s*(-?\d+(?:\.\d+)?)", joined)
            if m:
                out[axis.lower()] = float(m.group(1))
        return out

    def _check_limits(self, *, x: Optional[float], y: Optional[float], z: Optional[float]) -> None:
        checks = (
            ("X", x, self.x_limits),
            ("Y", y, self.y_limits),
            ("Z", z, self.z_limits),
        )
        for axis, value, limits in checks:
            if value is None or limits is None:
                continue
            low, high = limits
            if value < low or value > high:
                raise ValueError(f"{axis} target {value} is out of limits [{low}, {high}].")

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
            if self.auto_detect_port:
                self.port = self._auto_detect_prusa_port()
            if not self.port:
                raise ValueError(
                    "PrusaGcodeBackend.port is not set and auto-detection failed "
                    "(set explicit port, e.g., '/dev/ttyACM0' or 'COM5')."
                )

        self._ser = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
        time.sleep(0.8)  # allow printer to settle
        try:
            self._ser.reset_input_buffer()
            self._ser.reset_output_buffer()
        except Exception:
            pass

        self._connected = True
        self._last_state = {
            "connected": True,
            "port": self.port,
            "baudrate": self.baudrate,
            "position": dict(self._last_position),
        }

        # Safe: absolute mode only, no motion
        try:
            self.send_gcode("G90", timeout=2.0)
        except Exception:
            # Some firmwares may respond differently; don't fail hard here.
            pass

        # Best-effort initial position readback.
        try:
            lines = self.send_gcode("M114", timeout=2.5)
            parsed = self._parse_m114(lines)
            if parsed:
                self._last_position.update(parsed)
        except Exception:
            pass

        self._last_state["position"] = dict(self._last_position)

    def disconnect(self) -> None:
        if self._ser is not None:
            try:
                self._ser.close()
            except Exception:
                pass
        self._ser = None
        self._connected = False
        self._last_state = {"connected": False, "position": dict(self._last_position)}

    def home(self) -> None:
        # This WILL move the printer. Keep as explicit call.
        self.send_gcode("G28", timeout=30.0)
        try:
            lines = self.send_gcode("M114", timeout=3.0)
            parsed = self._parse_m114(lines)
            if parsed:
                self._last_position.update(parsed)
        except Exception:
            pass
        self._last_state["position"] = dict(self._last_position)

    def move_to(
        self,
        *,
        x: Optional[float] = None,
        y: Optional[float] = None,
        z: Optional[float] = None,
        feedrate: Optional[float] = None,
    ) -> None:
        # This WILL move the printer. Keep as explicit call.
        if x is None and y is None and z is None:
            raise ValueError("move_to requires at least one axis target (x, y, or z).")

        self._check_limits(x=x, y=y, z=z)

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

        if x is not None:
            self._last_position["x"] = float(x)
        if y is not None:
            self._last_position["y"] = float(y)
        if z is not None:
            self._last_position["z"] = float(z)
        self._last_state["position"] = dict(self._last_position)

    def get_state(self) -> Dict:
        # Best-effort live readback when connected.
        if self._connected:
            try:
                lines = self.send_gcode("M114", timeout=2.5)
                parsed = self._parse_m114(lines)
                if parsed:
                    self._last_position.update(parsed)
            except Exception:
                pass
        self._last_state["position"] = dict(self._last_position)
        return dict(self._last_state)

    def emergency_stop(self) -> None:
        # M112 is immediate emergency stop (firmware dependent)
        # This MAY stop heaters/motors. Use carefully.
        try:
            self.send_gcode("M112", timeout=2.0)
        finally:
            self.disconnect()
