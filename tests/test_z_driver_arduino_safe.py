import pytest

from core.z_control.z_driver_arduino_safe import ZDriverArduino


def test_z_driver_arduino_safe_dry_run_connect_move_disconnect():
    driver = ZDriverArduino(port="COM_TEST", baudrate=115200, dry_run=True)

    assert driver.connect() is True

    driver.move_to(20)
    driver.disconnect()

    assert driver.serial_conn is None
    assert driver.connected is False


def test_z_driver_arduino_safe_dry_run_approach_retract():
    driver = ZDriverArduino(port="COM_TEST", baudrate=115200, dry_run=True)

    assert driver.connect() is True

    driver.approach(start_z=20, target_z=17, step=1)
    assert driver.last_z_position == 17

    driver.retract(start_z=17, target_z=20, step=1)
    assert driver.last_z_position == 20

    driver.disconnect()
    assert driver.connected is False


def test_z_driver_arduino_safe_requires_connection_before_move():
    driver = ZDriverArduino(port="COM_TEST", baudrate=115200, dry_run=True)

    with pytest.raises(RuntimeError):
        driver.move_to(20)


def test_z_driver_arduino_safe_rejects_invalid_step():
    driver = ZDriverArduino(port="COM_TEST", baudrate=115200, dry_run=True)
    assert driver.connect() is True

    with pytest.raises(ValueError):
        driver.approach(start_z=20, target_z=17, step=0)

    with pytest.raises(ValueError):
        driver.retract(start_z=17, target_z=20, step=0)
