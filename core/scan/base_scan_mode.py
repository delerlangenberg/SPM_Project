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

    @abstractmethod
    def initialize(self):
        """
        Prepare scan environment, motors, and Z-feedback if needed.
        Called before scan loop starts.
        """
        pass

    @abstractmethod
    def perform_step(self):
        """
        Perform one scan step (X/Y movement, Z-feedback if needed, data acquisition).
        Return "done" to indicate completion.
        """
        pass

    @abstractmethod
    def finalize(self):
        """
        Safely stop all activities. Called after scan is complete or aborted.
        """
        pass

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
