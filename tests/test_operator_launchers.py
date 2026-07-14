from pathlib import Path


def test_short_batch_launcher_defaults_to_readonly_hardware():
    launcher = Path("spm.bat")
    source = launcher.read_text(encoding="utf-8")

    assert launcher.exists()
    assert "SPM_WEB_ALLOW_READONLY_HARDWARE=1" in source
    assert "SPM_WEB_ALLOW_HEALTH_MOTION=0" in source
    assert "SPM_WEB_ALLOW_REAL_SCAN=0" in source
    assert "SPM_WEB_ALLOW_FOIL_TAP=0" in source
    assert "SPM_WEB_ALLOW_Z_MOTION=0" in source
    assert "operator_workstation_software.py" in source


def test_short_powershell_launcher_defaults_to_readonly_hardware():
    launcher = Path("spm.ps1")
    source = launcher.read_text(encoding="utf-8")

    assert launcher.exists()
    assert '$env:SPM_WEB_ALLOW_READONLY_HARDWARE = "1"' in source
    assert '$env:SPM_WEB_ALLOW_HEALTH_MOTION = "0"' in source
    assert '$env:SPM_WEB_ALLOW_REAL_SCAN = "0"' in source
    assert '$env:SPM_WEB_ALLOW_FOIL_TAP = "0"' in source
    assert '$env:SPM_WEB_ALLOW_Z_MOTION = "0"' in source
    assert "operator_workstation_software.py" in source


def test_local_ai_batch_launcher_selects_open_source_provider():
    launcher = Path("spm_local_ai.bat")
    source = launcher.read_text(encoding="utf-8")

    assert launcher.exists()
    assert "SPM_AI_PROVIDER=local" in source
    assert "SPM_LOCAL_AI_BASE_URL=http://127.0.0.1:11434/v1" in source
    assert "SPM_LOCAL_AI_MODEL=qwen3-coder-next" in source
    assert "operator_workstation_software.py" in source


def test_local_ai_powershell_launcher_selects_open_source_provider():
    launcher = Path("spm_local_ai.ps1")
    source = launcher.read_text(encoding="utf-8")

    assert launcher.exists()
    assert '$env:SPM_AI_PROVIDER = "local"' in source
    assert '$env:SPM_LOCAL_AI_BASE_URL = "http://127.0.0.1:11434/v1"' in source
    assert '$env:SPM_LOCAL_AI_MODEL = "qwen3-coder-next"' in source
    assert "operator_workstation_software.py" in source
