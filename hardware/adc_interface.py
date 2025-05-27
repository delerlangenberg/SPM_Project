import random
import logging

class ADCInterface:
    """Handles ADC (Analog-to-Digital Conversion) for SPM data acquisition."""

    def __init__(self):
        self.adc_value = 0.0  # Placeholder for ADC value

    def read_signal(self):
        """Retrieves the ADC signal value."""
        return self.adc_value

    def adjust_position(self, adjustment):
        """Dummy function to simulate adjustment based on feedback."""
        self.adc_value += adjustment  # Simulates adjustment via feedback mechanism
        logging.info(f"ADC Position Adjusted by {adjustment:.3f}")


    def read_signal(self):
        """Retrieves the latest ADC signal value."""
        self.adc_value = round(random.uniform(0.0, 5.0), 2)  # Simulated ADC reading (0-5V range)
        logging.info(f"ADC Signal Read: {self.adc_value} V")
        return self.adc_value

    def calibrate_sensor(self):
        """Performs ADC calibration for accuracy."""
        logging.info("ADC Calibration started...")
        self.adc_value = 0.0  # Resetting ADC for recalibration
        logging.info("ADC Calibration completed.")

    def get_voltage_range(self):
        """Returns the allowed voltage range for ADC operation."""
        return {"min_voltage": 0.0, "max_voltage": 5.0}

# Example Usage:
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    adc_sensor = ADCInterface()
    adc_sensor.calibrate_sensor()
    
    for _ in range(3):
        print(f"ADC Reading: {adc_sensor.read_signal()} V")

def test_adc():
    print('Stub function test_adc called.')
