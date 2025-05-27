# simulation/tip_interaction_simulator.py

import numpy as np

class TipInteractionSimulator:
    """
    Simulates tip-sample interaction signals for STM and AFM modes.
    Useful for generating synthetic feedback responses based on distance.
    """

    def __init__(self, mode="afm_contact", noise_level=0.01):
        self.mode = mode.lower()
        self.noise_level = noise_level

    def get_response(self, z_distance):
        """
        Returns the simulated tip-sample interaction signal for a given z-distance.
        For AFM: force or amplitude response
        For STM: exponential tunneling current
        """
        base_signal = 0.0

        if self.mode == "stm":
            # Exponential decay: I ∝ exp(-kz)
            k = 1.5  # decay constant (arbitrary units)
            base_signal = np.exp(-k * z_distance)

        elif self.mode == "afm_contact":
            # Repulsive force increases quadratically when in contact
            contact_threshold = 0.2
            if z_distance < contact_threshold:
                base_signal = (contact_threshold - z_distance) ** 2
            else:
                base_signal = 0.0

        elif self.mode == "afm_non_contact":
            # Attractive van der Waals and amplitude reduction
            A0 = 1.0
            A = A0 * np.exp(-2.0 * z_distance)
            base_signal = A

        elif self.mode == "profile":
            # Profile mode assumes height = signal (ideal mapping)
            base_signal = z_distance

        else:
            raise ValueError(f"Unknown simulation mode: {self.mode}")

        # Add random noise
        noise = np.random.normal(0, self.noise_level)
        return max(0.0, base_signal + noise)
