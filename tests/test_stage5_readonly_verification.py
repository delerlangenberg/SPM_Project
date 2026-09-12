import pytest
from unittest.mock import MagicMock, patch

from tools.stage5_readonly_verification import run_stage5_verification


def test_stage5_verification_mocked():
    with patch("tools.stage5_readonly_verification.connect_real_hardware_readonly") as mock_mk4s, \
         patch("tools.stage5_readonly_verification.discover_mega_candidate_ports") as mock_ports, \
         patch("tools.stage5_readonly_verification.MegaProbeSerialTransport") as mock_mega_cls:

        mock_mk4s.return_value = {
            "ok": True,
            "port": "/dev/ttyACM0",
            "firmware": "Prusa-Firmware-Buddy 6.2.4",
            "machine_type": "Prusa-MK4",
            "temperature": "ok T:20 B:25",
            "endstops": "open",
            "position": "X:0 Y:0 Z:100",
            "safety": "no_movement",
            "dev_log_path_txt": "/tmp/test.txt",
            "dev_log_path_jsonl": "/tmp/test.jsonl",
        }
        mock_ports.return_value = ["/dev/ttyACM1"]

        mock_mega = MagicMock()
        mock_mega_cls.return_value.__enter__.return_value = mock_mega
        mock_mega.get_info.return_value = MagicMock(
            identity="SPM_PROBE_MEGA2560",
            firmware_version="0.8.7",
            protocol_version=1,
            wiring_revision="GROVE",
            hardware_verified=True,
            calibration_revision="CRT",
        )
        mock_mega.get_status.return_value = MagicMock(
            state="READY",
            trigger_raw=False,
            actuation_locked=True,
        )
        mock_mega.self_test.return_value = True

        result = run_stage5_verification()
        assert result["all_passed"] is True
        assert result["safety_checks"]["no_motion_verified"] is True

