@echo off
setlocal

cd /d "%~dp0"

set "SPM_WEB_ALLOW_READONLY_HARDWARE=1"
set "SPM_WEB_ALLOW_HEALTH_MOTION=1"
set "SPM_WEB_ALLOW_REAL_SCAN=1"
set "SPM_WEB_ALLOW_FOIL_TAP=1"

echo Starting SPM Prusa Operator Software with real-scan gates enabled...
echo Project: %CD%
echo.

".venv\Scripts\python.exe" "core\application\operator_workstation_software.py"

endlocal
