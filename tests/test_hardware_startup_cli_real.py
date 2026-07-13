import subprocess
import sys


def test_hardware_startup_cli_module_exists_and_help_is_not_required():
    result = subprocess.run(
        [sys.executable, "-m", "core.application.hardware_startup_cli"],
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )

    assert result.returncode == 0
    assert "success=True" in result.stdout
    assert "port=COM6" in result.stdout
    assert ">>> M115" in result.stdout
    assert ">>> M105" in result.stdout
    assert ">>> M119" in result.stdout
