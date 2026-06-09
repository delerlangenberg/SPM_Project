cd C:\SPM_Project
$env:PYTHONPATH="C:\SPM_Project"

Write-Host "SPM safe hardware demo: scan-profile validated baseline"

Write-Host "Running safe center test..."
.\.venv\Scripts\python.exe tools\safe_center_test.py

Write-Host "Running safe square test..."
.\.venv\Scripts\python.exe tools\safe_square_test.py

Write-Host "Running validated configured raster scan..."
.\.venv\Scripts\python.exe tools\run_configured_raster_scan.py

Write-Host "Regenerating raster plot..."
.\.venv\Scripts\python.exe tools\plot_safe_raster.py

Write-Host "Opening raster plot..."
start data\safe_raster_5x5_output.png

Write-Host "Safe hardware demo complete."
