import os
from types import SimpleNamespace

from core.application.modules.connection_manager import ConnectionManager, discover_ports
from core.web import mk4s_readonly_connection


def test_connect_enables_readonly_gate_but_no_motion_gate(monkeypatch) -> None:
    monkeypatch.setenv("SPM_WEB_ALLOW_READONLY_HARDWARE", "0")
    monkeypatch.setenv("SPM_WEB_ALLOW_REAL_MOTION", "0")
    applied = []
    manager = ConnectionManager(
        apply_port=applied.append,
        connect_backend=lambda **kwargs: {
            "ok": True, "connected": True, "status": "connected", "mode": "real_hardware_readonly", "port": kwargs["port"]
        },
        disconnect_backend=lambda: {"ok": True, "connected": False, "status": "disconnected"},
    )
    payload = manager.connect("COM6")
    assert payload["connected"] is True
    assert applied == ["COM6"]
    assert os.environ["SPM_WEB_ALLOW_READONLY_HARDWARE"] == "1"
    assert os.environ["SPM_WEB_ALLOW_REAL_MOTION"] == "0"
    assert manager.getStatus().state == "connected"


def test_disconnect_failure_preserves_connection() -> None:
    manager = ConnectionManager(
        apply_port=lambda _port: None,
        connect_backend=lambda **_kwargs: {"ok": True, "connected": True, "status": "connected", "port": "COM6"},
        disconnect_backend=lambda: (_ for _ in ()).throw(RuntimeError("serial close failed")),
    )
    manager.connect("COM6")
    payload = manager.disconnect()
    assert payload["status"] == "failed"
    assert manager.getStatus().connected is True


def test_backend_connect_exception_becomes_failed_status() -> None:
    manager = ConnectionManager(
        apply_port=lambda _port: None,
        connect_backend=lambda **_kwargs: (_ for _ in ()).throw(RuntimeError("port unavailable")),
        disconnect_backend=lambda: {},
    )
    assert manager.connect("COM9")["status"] == "failed"
    assert manager.getStatus().connected is False


def test_discover_ports_is_sorted_and_does_not_open_ports() -> None:
    ports = discover_ports(lambda: [
        SimpleNamespace(device="COM10", description="USB", hwid="B"),
        SimpleNamespace(device="COM2", description="MK4S", hwid="A"),
    ])
    assert [port.device for port in ports] == ["COM10", "COM2"]
    assert ports[1].description == "MK4S"


def test_simulation_status_never_calls_connection_backend() -> None:
    called = []
    manager = ConnectionManager(
        apply_port=lambda port: called.append(port),
        connect_backend=lambda **kwargs: called.append(kwargs) or {},
        disconnect_backend=lambda: {},
    )
    status = manager.set_simulation_mode(True)
    payload = manager.connect("COM6")
    assert status.state == "simulation"
    assert payload["mode"] == "simulation"
    assert called == []


def test_auto_detection_recognizes_prusa_identity_with_new_usb_pid(monkeypatch) -> None:
    monkeypatch.setattr(
        mk4s_readonly_connection,
        "list_serial_ports",
        lambda: [{"device": "COM6", "description": "Original Prusa MK4S", "hwid": "USB VID:PID=2C99:9999"}],
    )
    assert mk4s_readonly_connection.choose_prusa_port() == "COM6"
