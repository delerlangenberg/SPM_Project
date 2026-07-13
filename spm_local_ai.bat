@echo off
setlocal

cd /d "%~dp0"

set "SPM_WEB_ALLOW_READONLY_HARDWARE=1"
set "SPM_WEB_ALLOW_HEALTH_MOTION=1"
set "SPM_WEB_ALLOW_REAL_SCAN=1"
set "SPM_WEB_ALLOW_FOIL_TAP=1"

set "SPM_AI_PROVIDER=local"
set "SPM_LOCAL_AI_BASE_URL=http://127.0.0.1:11434/v1"
set "SPM_LOCAL_AI_CHAT_ENDPOINT=/chat/completions"
set "SPM_LOCAL_AI_MODEL=qwen3-coder-next"

echo Starting SPM Prusa Operator Software with local open-source AI...
echo Local AI: %SPM_LOCAL_AI_BASE_URL%  model=%SPM_LOCAL_AI_MODEL%
echo Project: %CD%
echo.

".venv\Scripts\python.exe" "core\application\operator_workstation_software.py"

endlocal
