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

def test_z_driver_arduino_safe_reports_dry_run_status():
    driver = ZDriverArduino(port="COM_TEST", baudrate=115200, dry_run=True)

    status = driver.get_status()
    assert status["mode"] == "DRY_RUN"
    assert status["connected"] is False
    assert status["serial_open"] is False
    assert status["last_command"] == "initialized"

    assert driver.connect() is True
    driver.move_to(12.5)

    status = driver.get_status()
    assert status["connected"] is True
    assert status["last_z_position"] == 12.5
    assert status["last_command"] == "move_to"

    driver.disconnect()

    status = driver.get_status()
    assert status["connected"] is False
    assert status["last_command"] == "disconnect"


def test_z_driver_arduino_safe_real_serial_mode_is_still_disabled():
    driver = ZDriverArduino(port="COM_TEST", baudrate=115200, dry_run=False)

    assert driver.mode_label() == "REAL_SERIAL_DISABLED"

    with pytest.raises(NotImplementedError):
        driver.connect()

def test_z_driver_arduino_safe_rejects_invalid_direction():
    driver = ZDriverArduino(port="COM_TEST", baudrate=115200, dry_run=True)
    assert driver.connect() is True

    with pytest.raises(ValueError):
        driver.approach(start_z=17, target_z=20, step=1)

    with pytest.raises(ValueError):
        driver.retract(start_z=20, target_z=17, step=1)

def test_z_driver_arduino_safe_reports_safe_to_move_only_when_connected_dry_run():
    dry_driver = ZDriverArduino(port="COM_TEST", baudrate=115200, dry_run=True)

    assert dry_driver.is_safe_to_move() is False

    assert dry_driver.connect() is True
    assert dry_driver.is_safe_to_move() is True

    dry_driver.disconnect()
    assert dry_driver.is_safe_to_move() is False

    real_disabled_driver = ZDriverArduino(port="COM_TEST", baudrate=115200, dry_run=False)
    assert real_disabled_driver.is_safe_to_move() is False

