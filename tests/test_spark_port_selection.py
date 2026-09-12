from types import SimpleNamespace
import pytest
from serial.tools import list_ports
from core.web import system_control as system


@pytest.fixture(autouse=True)
def preserve_state():
    previous = dict(system._SPM_SYSTEM_STATE)
    yield
    system._SPM_SYSTEM_STATE.clear()
    system._SPM_SYSTEM_STATE.update(previous)


def device(path, vid=0x2C99, pid=0x001A):
    return SimpleNamespace(device=path, vid=vid, pid=pid)


def test_linux_path_preserves_case(monkeypatch):
    monkeypatch.setattr(
        list_ports, "comports", lambda: [device("/dev/ttyACM0")]
    )
    assert system.system_apply_port("/dev/ttyACM0")["ok"]
    assert system._SPM_SYSTEM_STATE["manual_port"] == "/dev/ttyACM0"


def test_arduino_rejected_as_printer(monkeypatch):
    monkeypatch.setattr(
        list_ports, "comports",
        lambda: [device("/dev/ttyACM1", 0x2341, 0x0042)]
    )
    assert not system.system_apply_port("/dev/ttyACM1")["ok"]


def test_missing_port_preserves_previous_selection(monkeypatch):
    system._SPM_SYSTEM_STATE["manual_port"] = "/dev/ttyACM0"
    monkeypatch.setattr(list_ports, "comports", lambda: [])
    assert not system.system_apply_port("/dev/ttyACM9")["ok"]
    assert system._SPM_SYSTEM_STATE["manual_port"] == "/dev/ttyACM0"


def test_invalid_port_aborts_before_handshake(monkeypatch):
    from core.web import mk4s_readonly_connection

    monkeypatch.setenv("SPM_WEB_ALLOW_READONLY_HARDWARE", "1")
    monkeypatch.setattr(list_ports, "comports", lambda: [])

    def forbidden(**kwargs):
        pytest.fail("Handshake ran after port rejection.")

    monkeypatch.setattr(
        mk4s_readonly_connection, "connect_real_hardware_readonly", forbidden
    )
    assert not system.system_on(
        mode="hardware_readonly", port="/dev/ttyACM9"
    )["ok"]
