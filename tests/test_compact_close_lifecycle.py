from types import SimpleNamespace
from unittest.mock import Mock
import pytest
from tools.run_spm_control_compact import CompactControlWindow


@pytest.mark.parametrize(
    "approved,in_progress,accepted,requested",
    [
        (False, False, False, True),
        (False, True, False, False),
        (True, False, True, False),
    ],
)
def test_close_waits_for_success(approved, in_progress, accepted, requested):
    control = SimpleNamespace(
        _safe_close_approved=approved,
        _safe_close_in_progress=in_progress,
        request_safe_exit=Mock(),
    )
    window = SimpleNamespace(control=control, timer=Mock())
    event = Mock()

    CompactControlWindow.closeEvent(window, event)

    assert event.accept.called is accepted
    assert event.ignore.called is (not accepted)
    assert control.request_safe_exit.called is requested
    assert window.timer.stop.called is accepted
