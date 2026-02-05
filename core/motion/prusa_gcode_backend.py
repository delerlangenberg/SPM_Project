from typing import Dict, Optional

from core.motion.motion_backend import MotionBackend


class PrusaGcodeBackend(MotionBackend):
    """
    Motion backend using a Prusa MK4S (or compatible) printer
    controlled via G-code.

    This class intentionally starts as a stub.
    Hardware communication is added incrementally.
    """

    def __init__(self, *, port: Optional[str] = None, baudrate: int = 115200):
        self.port = port
        self.baudrate = baudrate
        self._connected = False

    def connect(self) -> None:
        raise NotImplementedError("PrusaGcodeBackend.connect not implemented yet")

    def disconnect(self) -> None:
        raise NotImplementedError("PrusaGcodeBackend.disconnect not implemented yet")

    def home(self) -> None:
        raise NotImplementedError("PrusaGcodeBackend.home not implemented yet")

    def move_to(
        self,
        *,
        x: Optional[float] = None,
        y: Optional[float] = None,
        z: Optional[float] = None,
        feedrate: Optional[float] = None,
    ) -> None:
        raise NotImplementedError("PrusaGcodeBackend.move_to not implemented yet")

    def get_state(self) -> Dict:
        raise NotImplementedError("PrusaGcodeBackend.get_state not implemented yet")

    def emergency_stop(self) -> None:
        raise NotImplementedError("PrusaGcodeBackend.emergency_stop not implemented yet")
