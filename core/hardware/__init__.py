"""Physical-device integrations used by the SPM Operator application."""
"""Physical hardware integration boundaries for SPM Operator."""

from .spm_system import (
    AcquisitionMode,
    SpmPortMap,
    SpmReadinessReport,
    UsbPortIdentity,
    discover_spm_ports,
    evaluate_spm_readiness,
)

__all__ = [
    "AcquisitionMode",
    "SpmPortMap",
    "SpmReadinessReport",
    "UsbPortIdentity",
    "discover_spm_ports",
    "evaluate_spm_readiness",
]
