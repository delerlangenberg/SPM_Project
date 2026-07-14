$ErrorActionPreference = "Stop"

Set-Location -LiteralPath $PSScriptRoot

$env:SPM_WEB_ALLOW_READONLY_HARDWARE = "1"
$env:SPM_WEB_ALLOW_HEALTH_MOTION = "0"
$env:SPM_WEB_ALLOW_REAL_SCAN = "0"
$env:SPM_WEB_ALLOW_FOIL_TAP = "0"
$env:SPM_WEB_ALLOW_Z_MOTION = "0"

$env:SPM_AI_PROVIDER = "deepseek"
$env:SPM_DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"
$env:SPM_DEEPSEEK_MODEL = "deepseek-chat"

Write-Host "Starting SPM Prusa Operator Software with DeepSeek AI..."
Write-Host "DeepSeek: $env:SPM_DEEPSEEK_BASE_URL  model=$env:SPM_DEEPSEEK_MODEL"
Write-Host "Project: $PWD"
Write-Host ""

& ".\.venv\Scripts\python.exe" "core\application\operator_workstation_software.py"
