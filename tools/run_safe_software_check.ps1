cd C:\SPM_Project
$env:PYTHONPATH="C:\SPM_Project"

Write-Host "SPM safe software check: scan-profile validated baseline"

Write-Host "Running pytest..."
.\.venv\Scripts\python.exe -m pytest -v

Write-Host "Running CLI scan launcher dry run..."
.\.venv\Scripts\python.exe core\application\cli_scan_launcher.py --dry-run

Write-Host "Running Prusa ping, no motion..."
.\.venv\Scripts\python.exe tools\prusa_ping.py --port COM5 --no-auto-detect

Write-Host "Running plot generation..."
.\.venv\Scripts\python.exe tools\plot_safe_raster.py

Write-Host "Done."
