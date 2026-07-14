$ErrorActionPreference = "Stop"

Set-Location -LiteralPath $PSScriptRoot

$env:SPM_WEB_ALLOW_READONLY_HARDWARE = "1"
$env:SPM_WEB_ALLOW_HEALTH_MOTION = "0"
$env:SPM_WEB_ALLOW_REAL_SCAN = "0"
$env:SPM_WEB_ALLOW_FOIL_TAP = "0"
$env:SPM_WEB_ALLOW_Z_MOTION = "0"

Write-Host "Starting SPM Prusa Operator Software with real-scan gates enabled..."
Write-Host "Project: $PWD"
Write-Host ""

& ".\.venv\Scripts\python.exe" "core\application\operator_workstation_software.py"
