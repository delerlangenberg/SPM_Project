cd C:\SPM_Project
$env:PYTHONPATH="C:\SPM_Project"

Write-Host "Running SPM CLI scan launcher dry run..."
.\.venv\Scripts\python.exe core\application\cli_scan_launcher.py --dry-run

Write-Host "CLI dry run complete."
