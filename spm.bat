@echo off
setlocal enabledelayedexpansion

cd /d "%~dp0"

set SPM_WEB_ALLOW_READONLY_HARDWARE=1
set SPM_WEB_ALLOW_HEALTH_MOTION=1
set SPM_WEB_ALLOW_REAL_SCAN=1
set SPM_WEB_ALLOW_FOIL_TAP=1
set SPM_AI_PROVIDER=deepseek
set SPM_DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
set SPM_DEEPSEEK_MODEL=deepseek-chat

if not defined SPM_DEEPSEEK_API_KEY (
    if exist config\\deepseek_key.txt (
        set /p SPM_DEEPSEEK_API_KEY=<config\\deepseek_key.txt
    )
)

if defined SPM_DEEPSEEK_API_KEY (
    echo DeepSeek AI: enabled (\model=%SPM_DEEPSEEK_MODEL%\)
) else (
    echo DeepSeek AI: not configured - set SPM_DEEPSEEK_API_KEY or create config\\deepseek_key.txt
)

echo Starting SPM Prusa MK4S v0.2.24...
echo.
".venv\Scripts\python.exe" "core\application\operator_workstation_software.py"
endlocal
