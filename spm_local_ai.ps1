$ErrorActionPreference = "Stop"

Set-Location -LiteralPath $PSScriptRoot

$env:SPM_WEB_ALLOW_READONLY_HARDWARE = "1"
$env:SPM_WEB_ALLOW_HEALTH_MOTION = "1"
$env:SPM_WEB_ALLOW_REAL_SCAN = "1"
$env:SPM_WEB_ALLOW_FOIL_TAP = "1"

$env:SPM_AI_PROVIDER = "local"
$env:SPM_LOCAL_AI_BASE_URL = "http://127.0.0.1:11434/v1"
$env:SPM_LOCAL_AI_CHAT_ENDPOINT = "/chat/completions"
$env:SPM_LOCAL_AI_MODEL = "qwen3-coder-next"

Write-Host "Starting SPM Prusa Operator Software with local open-source AI..."
Write-Host "Local AI: $env:SPM_LOCAL_AI_BASE_URL  model=$env:SPM_LOCAL_AI_MODEL"
Write-Host "Project: $PWD"
Write-Host ""

& ".\.venv\Scripts\python.exe" "core\application\operator_workstation_software.py"
