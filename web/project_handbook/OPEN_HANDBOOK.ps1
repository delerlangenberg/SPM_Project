$ErrorActionPreference = "Stop"

$handbookRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$handbookUrl = "http://localhost:4310"
$offlineIndex = Join-Path $handbookRoot "index.html"
$logFolder = Join-Path $handbookRoot ".local"
$stdoutLog = Join-Path $logFolder "handbook-server.log"
$stderrLog = Join-Path $logFolder "handbook-server-error.log"

function Test-HandbookServer {
    try {
        $response = Invoke-WebRequest -Uri $handbookUrl -UseBasicParsing -TimeoutSec 1
        return $response.StatusCode -ge 200 -and $response.StatusCode -lt 500
    }
    catch {
        return $false
    }
}

if (-not (Test-HandbookServer)) {
    $npmCommand = Get-Command npm.cmd -ErrorAction SilentlyContinue
    if ($null -eq $npmCommand) {
        Start-Process -FilePath $offlineIndex
        exit 0
    }

    New-Item -ItemType Directory -Force -Path $logFolder | Out-Null
    Start-Process `
        -FilePath $npmCommand.Source `
        -ArgumentList @("run", "dev", "--", "--host", "localhost", "--port", "4310") `
        -WorkingDirectory $handbookRoot `
        -WindowStyle Hidden `
        -RedirectStandardOutput $stdoutLog `
        -RedirectStandardError $stderrLog

    foreach ($attempt in 1..30) {
        Start-Sleep -Milliseconds 500
        if (Test-HandbookServer) {
            break
        }
    }
}

if (Test-HandbookServer) {
    Start-Process $handbookUrl
}
else {
    Start-Process -FilePath $offlineIndex
}
