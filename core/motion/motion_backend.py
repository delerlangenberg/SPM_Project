from abc import ABC, abstractmethod
from typing import Optional, Dict


class MotionBackend(ABC):
    """
    Abstract interface for any motion system used by the SPM.

    Implementations may be:
    - simulated
    - real hardware
    - G-code driven systems (e.g. Prusa MK4S)
    """

    @abstractmethod
    def connect(self) -> None:
        """Establish connection to the motion system."""
        raise NotImplementedError

    @abstractmethod
    def disconnect(self) -> None:
        """Safely disconnect from the motion system."""
        raise NotImplementedError

    @abstractmethod
    def home(self) -> None:
        """Home all relevant axes."""
        raise NotImplementedError

    @abstractmethod
    def move_to(
        self,
        *,
        x: Optional[float] = None,
        y: Optional[float] = None,
        z: Optional[float] = None,
        feedrate: Optional[float] = None,
    ) -> None:
        """
        Move to an absolute position.
        Any axis set to None must remain unchanged.
        """
        raise NotImplementedError

    @abstractmethod
    def get_state(self) -> Dict:
        """
        Return current motion state (position, status, errors if available).
        """
        raise NotImplementedError

    @abstractmethod
    def emergency_stop(self) -> None:
        """Immediately stop all motion."""
        raise NotImplementedError
