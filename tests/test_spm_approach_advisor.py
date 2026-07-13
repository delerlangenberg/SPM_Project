from core.ai.spm_approach_advisor import ApproachAdvisorInput, advise_approach


def test_approach_advisor_accepts_coherent_surface_search():
    payload = advise_approach(
        ApproachAdvisorInput(
            z_setpoint_mm=4.0,
            tapping_range_mm=12.0,
            expected_surface_z_mm=8.0,
            approach_speed_mm_s=1.0,
            full_retract_z_mm=120.0,
            latest_z_mm=120.0,
            connected=True,
        )
    )

    assert payload["ok"] is True
    assert payload["risk"] == "ready"
    assert payload["tap_start_z_mm"] == 16.0
    assert "coherent" in " ".join(payload["recommendations"])


def test_approach_advisor_blocks_when_setpoint_cannot_reach_surface():
    payload = advise_approach(
        ApproachAdvisorInput(
            z_setpoint_mm=10.0,
            tapping_range_mm=5.0,
            expected_surface_z_mm=8.0,
            approach_speed_mm_s=1.0,
            full_retract_z_mm=120.0,
            latest_z_mm=120.0,
            connected=True,
        )
    )

    assert payload["ok"] is False
    assert payload["risk"] == "blocked"
    assert "Lower the Z setpoint" in " ".join(payload["recommendations"])


def test_approach_advisor_warns_on_fast_experimental_contact_speed():
    payload = advise_approach(
        ApproachAdvisorInput(
            z_setpoint_mm=4.0,
            tapping_range_mm=12.0,
            expected_surface_z_mm=8.0,
            approach_speed_mm_s=5.0,
            full_retract_z_mm=120.0,
            latest_z_mm=120.0,
            connected=True,
        )
    )

    assert payload["ok"] is True
    assert payload["risk"] == "caution"
    assert "reduce approach speed" in " ".join(payload["recommendations"])


def test_approach_advisor_blocks_until_system_is_connected():
    payload = advise_approach(
        ApproachAdvisorInput(
            z_setpoint_mm=4.0,
            tapping_range_mm=12.0,
            expected_surface_z_mm=8.0,
            approach_speed_mm_s=1.0,
            full_retract_z_mm=120.0,
            latest_z_mm=120.0,
            connected=False,
        )
    )

    assert payload["ok"] is False
    assert payload["risk"] == "blocked"
    assert "Connect Phase 2.1" in " ".join(payload["recommendations"])
