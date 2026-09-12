import pytest
from core.application.modules.connection_manager import ConnectionManager


@pytest.fixture
def setup_manager(monkeypatch):
    monkeypatch.setenv("SPM_WEB_ALLOW_READONLY_HARDWARE", "1")
    calls = []

    def apply(port):
        calls.append(("port", port))
        return {"ok": True}

    def connect(**kwargs):
        calls.append(("connect", kwargs))
        return {
            "ok": True, "connected": True, "ready": True,
            "status": "connected", "port": kwargs["port"],
        }

    def disconnect():
        calls.append(("disconnect",))
        return {"ok": True, "connected": False, "status": "disconnected"}

    manager = ConnectionManager(
        connect_backend=connect, disconnect_backend=disconnect,
        apply_port=apply,
    )
    return manager, calls


def test_disabled_gate_never_calls_backend(setup_manager, monkeypatch):
    manager, calls = setup_manager
    monkeypatch.setenv("SPM_WEB_ALLOW_READONLY_HARDWARE", "0")
    result = manager.connect("/dev/spm-mk4s")
    assert not result["ok"]
    assert calls == []
    assert not manager.getStatus().busy


def test_rejected_port_never_connects(setup_manager):
    manager, calls = setup_manager
    manager._apply_port = lambda port: {
        "ok": False, "message": "Wrong device"
    }
    result = manager.connect("/dev/spm-arduino")
    assert not result["ok"]
    assert calls == []
    assert not manager.getStatus().connected


def test_auto_clears_previous_manual_selection(setup_manager):
    manager, calls = setup_manager
    manager.connect("")
    assert calls[0] == ("port", "")
    assert calls[1] == (
        "connect", {"mode": "hardware_readonly", "port": ""}
    )


def test_explicit_disconnected_overrides_ready(setup_manager):
    manager, _ = setup_manager
    manager.accept_payload({
        "connected": False, "ready": True, "status": "simulation"
    })
    assert not manager.getStatus().connected


def test_connect_disconnect_reconnect(setup_manager):
    manager, calls = setup_manager
    for _ in range(2):
        assert manager.connect("/dev/spm-mk4s")["ok"]
        assert manager.getStatus().connected
        assert manager.disconnect()["ok"]
        assert not manager.getStatus().connected
        assert not manager.getStatus().busy
    assert sum(call[0] == "connect" for call in calls) == 2
    assert sum(call[0] == "disconnect" for call in calls) == 2
