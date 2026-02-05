# core/scan/base_scan_mode.py

from abc import ABC, abstractmethod


class BaseScanMode(ABC):
    """
    Abstract base class for all scan modes (STM, AFM-Contact, AFM-NonContact, Profiling).
    """

    def __init__(self, config=None):
        self.config = config or {}
        self.current_position = (0, 0)
        self.data_buffer = []

    def initialize(self):
        """Default no-op initialize (override in subclasses)."""
        return None

    def perform_step(self):
        """Default step returns 'done' (override in subclasses)."""
        return "done"

    def finalize(self):
        """Default no-op finalize (override in subclasses)."""
        return None


    def get_data(self):
        """
        Return the accumulated scan data buffer.
        """
        return self.data_buffer

    def set_config(self, config):
        """
        Apply new scan configuration at runtime.
        """
        self.config = config
