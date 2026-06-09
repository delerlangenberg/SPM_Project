from core.z_control.z_driver_arduino_safe import ZDriverArduino


def test_z_driver_arduino_safe_dry_run_connect_move_disconnect():
    driver = ZDriverArduino(port="COM_TEST", baudrate=115200, dry_run=True)

    assert driver.connect() is True

    driver.move_to(20)
    driver.disconnect()

    assert driver.serial_conn is None
