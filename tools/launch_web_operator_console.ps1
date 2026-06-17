param(
    [int]$Port = 8787,
    [switch]$NoBrowser
)

$ErrorActionPreference = "Stop"

$project = "D:\SPM_Prusa_Project"
$python = Join-Path $project ".venv\Scripts\python.exe"
$url = "http://127.0.0.1:$Port"

Set-Location $project

Write-Host "=== SPM PRUSA WEB CONSOLE LAUNCHER ==="

$connections = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
if ($connections) {
    foreach ($c in $connections) {
        Write-Host "Stopping existing server process: $($c.OwningProcess)"
        Stop-Process -Id $c.OwningProcess -Force -ErrorAction SilentlyContinue
    }
}

$stdout = Join-Path $env:TEMP "spm_web_console_stdout.txt"
$stderr = Join-Path $env:TEMP "spm_web_console_stderr.txt"

Remove-Item $stdout -Force -ErrorAction SilentlyContinue
Remove-Item $stderr -Force -ErrorAction SilentlyContinue

$server = Start-Process -FilePath $python `
    -ArgumentList "tools\run_web_operator_console.py --host 127.0.0.1 --port $Port" `
    -WorkingDirectory $project `
    -RedirectStandardOutput $stdout `
    -RedirectStandardError $stderr `
    -WindowStyle Hidden `
    -PassThru

Write-Host "Server process id: $($server.Id)"
Write-Host "URL: $url"

$ok = $false
for ($i = 1; $i -le 20; $i++) {
    Start-Sleep -Milliseconds 500
    try {
        $response = Invoke-WebRequest -Uri "$url/api/status" -UseBasicParsing -TimeoutSec 2
        if ($response.StatusCode -eq 200) {
            Write-Host "Server OK after attempt: $i"
            $ok = $true
            break
        }
    } catch {
        Write-Host "waiting_attempt_$i"
    }
}

if (-not $ok) {
    Write-Host "SERVER FAILED"
    Write-Host "=== STDERR ==="
    if (Test-Path $stderr) { Get-Content $stderr -Raw }
    exit 1
}

if (-not $NoBrowser) {
    Start-Process $url
}

Write-Host "To stop later:"
Write-Host "Stop-Process -Id $($server.Id)"
