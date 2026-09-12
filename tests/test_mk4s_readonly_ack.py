import pytest
from core.web import mk4s_readonly_connection as connection


class Logger:
    def emit(self, *args, **kwargs):
        pass

    def emit_raw(self, *args, **kwargs):
        pass


class Transport:
    def __init__(self, responses=(), short_write=False):
        self.responses = iter(responses)
        self.writes = []
        self.short_write = short_write

    def write(self, data):
        self.writes.append(data)
        return len(data) - 1 if self.short_write else len(data)

    def readline(self):
        return next(self.responses, b"")


@pytest.mark.parametrize("reply", [b"ok\n", b"ok T:22.0 /0.0\n"])
def test_acknowledgement_is_accepted(reply):
    transport = Transport([reply])
    result = connection._send_readonly_command(
        transport, "M105", 1, Logger()
    )
    assert result[-1].startswith("ok")
    assert transport.writes == [b"M105\n"]


def test_missing_acknowledgement_fails(monkeypatch):
    clock = iter([0.0, 0.0, 2.0])
    monkeypatch.setattr(connection.time, "monotonic", lambda: next(clock))
    with pytest.raises(TimeoutError):
        connection._send_readonly_command(
            Transport([b"X:1 Y:2 Z:3\n"]), "M114", 1, Logger()
        )


@pytest.mark.parametrize("reply", [b"Error: rejected\n", b"Resend: 1\n"])
def test_printer_error_fails(reply):
    with pytest.raises(RuntimeError):
        connection._send_readonly_command(
            Transport([reply, b"ok\n"]), "M115", 1, Logger()
        )


def test_motion_command_is_rejected_before_write():
    transport = Transport()
    with pytest.raises(ValueError):
        connection._send_readonly_command(
            transport, "G90", 1, Logger()
        )
    assert transport.writes == []


def test_partial_write_fails():
    with pytest.raises(OSError):
        connection._send_readonly_command(
            Transport(short_write=True), "M115", 1, Logger()
        )
