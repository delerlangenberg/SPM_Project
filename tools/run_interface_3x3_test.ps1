cd C:\SPM_Project
$env:PYTHONPATH="C:\SPM_Project"

Write-Host "Running SPM interface 3x3 hardware test..."
Write-Host "This writes only to data\interface_test_output.csv"
Write-Host "The 5x5 baseline output is not touched."

.\.venv\Scripts\python.exe core\application\cli_scan_launcher.py `
  --execute-hardware `
  --x-min 48 `
  --x-max 52 `
  --y-min 48 `
  --y-max 52 `
  --z 20 `
  --x-resolution 3 `
  --y-resolution 3 `
  --output-file data\interface_test_output.csv

Write-Host "Generating interface test plot..."

.\.venv\Scripts\python.exe tools\plot_safe_raster.py `
  --input-file data\interface_test_output.csv `
  --output-file data\interface_test_output.png `
  --cmap plasma

Write-Host "Opening interface test plot..."
start data\interface_test_output.png

Write-Host "Interface 3x3 hardware test complete."
