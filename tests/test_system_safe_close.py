from core.web import system_control


def test_safe_close_standby_uses_default_target_without_prior_diagnosis(monkeypatch):
    previous_state = dict(system_control._SPM_SYSTEM_STATE)

    def fake_standby(port=None):
        return {
            "ok": True,
            "port": port or "COM6",
            "position": {"x": 125.0, "y": 105.0, "z": 120.0},
            "position_z": 120.0,
            "safe_standby": {"x": 125.0, "y": 105.0, "z": 120.0},
            "log_lines": ["SAFE STANDBY COMPLETE"],
        }

    try:
        system_control._SPM_SYSTEM_STATE.update(
            {
                "mode": "real_hardware_readonly",
                "connected": True,
                "powered": True,
                "ready": True,
                "port": "COM6",
                "motion_verified": False,
            }
        )
        monkeypatch.setenv("SPM_WEB_ALLOW_HEALTH_MOTION", "1")
        monkeypatch.setattr("core.web.mk4s_health_motion.run_mk4s_safe_standby", fake_standby)

        payload = system_control.system_safe_standby_for_close()

        assert payload["ok"] is True
        assert payload["status"] == "safe_standby"
        assert payload["position"] == "X:125.00 Y:105.00 Z:120.00"
        assert "SAFE CLOSE: attempting default standby X125 Y105 Z120." in payload["log_lines"]
    finally:
        system_control._SPM_SYSTEM_STATE.clear()
        system_control._SPM_SYSTEM_STATE.update(previous_state)


def test_safe_close_standby_still_requires_motion_gate(monkeypatch):
    previous_state = dict(system_control._SPM_SYSTEM_STATE)
    try:
        system_control._SPM_SYSTEM_STATE.update(
            {
                "mode": "real_hardware_readonly",
                "connected": True,
                "powered": True,
                "ready": True,
                "port": "COM6",
            }
        )
        monkeypatch.delenv("SPM_WEB_ALLOW_HEALTH_MOTION", raising=False)

        payload = system_control.system_safe_standby_for_close()

        assert payload["ok"] is False
        assert payload["mode"] == "safe_close_motion_locked"
        assert "SPM_WEB_ALLOW_HEALTH_MOTION" in " ".join(payload["log_lines"])
    finally:
        system_control._SPM_SYSTEM_STATE.clear()
        system_control._SPM_SYSTEM_STATE.update(previous_state)
