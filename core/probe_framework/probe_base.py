from abc import ABC, abstractmethod
from typing import Any, Dict

from .probe_types import ProbeIdentity


class ProbeBase(ABC):
    def __init__(self, identity: ProbeIdentity) -> None:
        self.identity = identity
        self.connected = False

    @abstractmethod
    def connect(self) -> Dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def disconnect(self) -> Dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def deploy(self) -> Dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def retract(self) -> Dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def read(self) -> Dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def calibrate(self) -> Dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def status(self) -> Dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def identify(self) -> Dict[str, Any]:
        raise NotImplementedError
