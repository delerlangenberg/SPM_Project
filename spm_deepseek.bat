@echo off
setlocal

cd /d "%~dp0"

set "SPM_WEB_ALLOW_READONLY_HARDWARE=1"
set "SPM_WEB_ALLOW_HEALTH_MOTION=0"
set "SPM_WEB_ALLOW_REAL_SCAN=0"
set "SPM_WEB_ALLOW_FOIL_TAP=0"
set "SPM_WEB_ALLOW_Z_MOTION=0"

set "SPM_AI_PROVIDER=deepseek"
set "SPM_DEEPSEEK_BASE_URL=https://api.deepseek.com/v1"
set "SPM_DEEPSEEK_MODEL=deepseek-chat"

echo Starting SPM Prusa Operator Software with DeepSeek AI...
echo DeepSeek: %SPM_DEEPSEEK_BASE_URL%  model=%SPM_DEEPSEEK_MODEL%
echo Project: %CD%
echo.

".venv\Scripts\python.exe" "core\application\operator_workstation_software.py"

endlocal
