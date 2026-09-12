param(
    [switch]$ConfirmCleanup
)

$ErrorActionPreference = "Stop"
$root = [System.IO.Path]::GetFullPath("C:\SPM_Prusa_Project")

$obsolete = @(
    ".pytest_cache",
    "build",
    "dist",
    "tmp",
    "docs\versions",
    "docs\emergency_build_20260617",
    "docs\webui_backup_20260617",
    "docs\old_gui_review_20260617",
    "tests_legacy",
    "installer\windows\releases",
    "installer\windows\latest",
    "installer\windows\logs",
    "installer\windows\uninstall",
    "installer\linux",
    "installer\macos"
)

Write-Host "SPM project cleanup"
Write-Host "Keeps:"
Write-Host "  installer\windows\SPM_Operator_Setup.exe"
Write-Host "  installer\windows\BUILD_INFO.txt"
Write-Host "  backups\phase_milestones\SPM_Prusa_Project_Phase_1_8G_Professional_Stable_Checkpoint_2026-06-16.zip"
Write-Host ""

foreach ($relative in $obsolete) {
    $target = [System.IO.Path]::GetFullPath((Join-Path $root $relative))
    $prefix = $root.TrimEnd("\") + "\"
    if (-not $target.StartsWith($prefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing unsafe path: $target"
    }

    if (Test-Path -LiteralPath $target) {
        if ($ConfirmCleanup) {
            Remove-Item -LiteralPath $target -Recurse -Force
            Write-Host "Removed: $relative"
        } else {
            Write-Host "Would remove: $relative"
        }
    }
}

if (-not $ConfirmCleanup) {
    Write-Host ""
    Write-Host "Preview only. Run again with -ConfirmCleanup to remove these generated and superseded files."
}
