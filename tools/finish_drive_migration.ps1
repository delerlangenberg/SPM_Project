param(
    [switch]$ConfirmMigrationCleanup
)

$ErrorActionPreference = "Stop"
$sourceRoot = [System.IO.Path]::GetFullPath("D:\SPM_Prusa_Project")
$destinationRoot = [System.IO.Path]::GetFullPath("C:\SPM_Prusa_Project")
$backupRoot = [System.IO.Path]::GetFullPath("D:\SPM_Prusa_Project\backups")

if ($sourceRoot -ne "D:\SPM_Prusa_Project") {
    throw "Unexpected source path: $sourceRoot"
}
if ($destinationRoot -ne "C:\SPM_Prusa_Project") {
    throw "Unexpected destination path: $destinationRoot"
}
if (-not (Test-Path -LiteralPath $destinationRoot -PathType Container)) {
    throw "Verified C: destination is missing."
}
if (-not (Test-Path -LiteralPath $backupRoot -PathType Container)) {
    throw "D: backup directory is missing."
}

$targets = Get-ChildItem -LiteralPath $sourceRoot -Force |
    Where-Object { $_.Name -ne "backups" }

foreach ($target in $targets) {
    $resolved = [System.IO.Path]::GetFullPath($target.FullName)
    $expectedPrefix = $sourceRoot.TrimEnd("\") + "\"

    if (-not $resolved.StartsWith(
        $expectedPrefix,
        [System.StringComparison]::OrdinalIgnoreCase
    )) {
        throw "Refusing path outside the old project: $resolved"
    }
    if ($resolved.Equals(
        $backupRoot,
        [System.StringComparison]::OrdinalIgnoreCase
    )) {
        throw "Refusing to remove the backup directory."
    }

    if ($ConfirmMigrationCleanup) {
        Remove-Item -LiteralPath $resolved -Recurse -Force
        Write-Host "Removed old working item: $($target.Name)"
    } else {
        Write-Host "Would remove old working item: $($target.Name)"
    }
}

if (-not $ConfirmMigrationCleanup) {
    Write-Host "Preview only. Add -ConfirmMigrationCleanup after verification."
}
