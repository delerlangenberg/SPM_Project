from dataclasses import dataclass
from enum import Enum


class ProbeKind(str, Enum):
    CR_TOUCH = "cr_touch"
    PIEZO = "piezo"
    OPTICAL = "optical"
    CAPACITIVE = "capacitive"
    LASER = "laser"
    STM = "stm"
    AFM = "afm"
    CUSTOM = "custom"


@dataclass(frozen=True)
class ProbeIdentity:
    probe_id: str
    kind: ProbeKind
    name: str
    hardware_enabled: bool = False
