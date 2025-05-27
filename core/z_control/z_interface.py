# z_interface.py

from core.z_control.z_driver_arduino import ArduinoZDriver
from core.z_control.z_driver_simulated import SimulatedZDriver

# core/z_control/z_interface.py

def launch_z_interface():
    print("[Z-Control Interface] Launching z-control interface...")


def get_z_driver(mode='simulated'):
    """
    Factory method to get the appropriate Z-axis driver.

    Args:
        mode (str): 'simulated' or 'hardware'

    Returns:
        Instance of Z-driver (simulated or hardware).
    """
    if mode == 'hardware':
        return ArduinoZDriver()
    else:
        return SimulatedZDriver()

def launch_z_interface():
    print('Stub function launch_z_interface called.')
