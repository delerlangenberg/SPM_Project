param(
    [int]$Port = 8787
)

$ErrorActionPreference = "Stop"

# Phase 2.2D: allow safe real-hardware read-only handshake from browser Connect.
# This does NOT allow motion, homing, heating, or printer writes.
$env:SPM_WEB_ALLOW_READONLY_HARDWARE = "1"
$env:SPM_WEB_ALLOW_HEALTH_MOTION = "0"

$ProjectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $ProjectRoot

$PythonExe = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$ServerScript = Join-Path $ProjectRoot "core\web\operator_console_server.py"
$Url = "http://127.0.0.1:$Port"

Write-Host "=== SPM PRUSA WEB CONSOLE LAUNCHER ==="

if (-not (Test-Path $PythonExe)) {
    throw "Python virtual environment not found: $PythonExe"
}

if (-not (Test-Path $ServerScript)) {
    throw "Web console server not found: $ServerScript"
}

# Stop any process already listening on the requested port.
try {
    $connections = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
} catch {
    $connections = @()
}

$processIds = @($connections | Select-Object -ExpandProperty OwningProcess -Unique)

foreach ($pidToStop in $processIds) {
    if ($pidToStop -and $pidToStop -ne $PID) {
        Write-Host "Stopping existing server process: $pidToStop"
        Stop-Process -Id $pidToStop -Force -ErrorAction SilentlyContinue
    }
}

Start-Sleep -Milliseconds 500

# Start web operator console.
$argumentList = @(
    $ServerScript,
    "--port",
    "$Port"
)

$process = Start-Process `
    -FilePath $PythonExe `
    -ArgumentList $argumentList `
    -WorkingDirectory $ProjectRoot `
    -PassThru `
    -WindowStyle Hidden

Write-Host "Server process id: $($process.Id)"
Write-Host "URL: $Url"

$serverReady = $false

for ($attempt = 1; $attempt -le 20; $attempt++) {
    Start-Sleep -Milliseconds 300

    try {
        $response = Invoke-WebRequest -Uri "$Url/api/status" -UseBasicParsing -TimeoutSec 2
        if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 500) {
            Write-Host "Server OK after attempt: $attempt"
            $serverReady = $true
            break
        }
    } catch {
        # Continue waiting.
    }

    if ($process.HasExited) {
        throw "Server process exited early with code $($process.ExitCode)."
    }
}

if (-not $serverReady) {
    throw "Server did not become ready at $Url"
}

Write-Host "To stop later:"
Write-Host "Stop-Process -Id $($process.Id)"

Start-Process $Url


