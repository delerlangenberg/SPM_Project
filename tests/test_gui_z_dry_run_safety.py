from pathlib import Path


def test_gui_contains_z_dry_run_limit_validation():
    text = Path("core/application/gui_scan_launcher.py").read_text(encoding="utf-8")

    assert "self.limits.z_min <= z_position <= self.limits.z_max" in text
    assert "outside safe limits" in text
    assert "Invalid Z test value" in text
    assert "Z dry-run status: Last move OK" in text


def test_gui_contains_z_dry_run_approach_retract_controls():
    text = Path("core/application/gui_scan_launcher.py").read_text(encoding="utf-8")

    assert "Z Dry Run: Approach" in text
    assert "Z Dry Run: Retract" in text
    assert "self.z_approach_start" in text
    assert "self.z_approach_target" in text
    assert "self.z_retract_start" in text
    assert "self.z_retract_target" in text
    assert "self.z_step_size" in text


def test_gui_contains_z_dry_run_approach_retract_safety_validation():
    text = Path("core/application/gui_scan_launcher.py").read_text(encoding="utf-8")

    assert "def run_z_dry_approach" in text
    assert "def run_z_dry_retract" in text
    assert "step_size <= 0" in text
    assert "self.limits.z_min <= start_z <= self.limits.z_max" in text
    assert "self.limits.z_min <= target_z <= self.limits.z_max" in text
    assert "Invalid approach direction" in text
    assert "Invalid retract direction" in text
    assert "self.z_driver.approach" in text
    assert "self.z_driver.retract" in text
    assert "Z dry-run status: Approach OK" in text
    assert "Z dry-run status: Retract OK" in text
