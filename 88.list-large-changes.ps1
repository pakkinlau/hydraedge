<#
.SYNOPSIS
    List untracked or modified files ≥ 95 MB.
#>
param(
    [long]$Threshold = 95MB
)

# Gather paths: modified vs HEAD + untracked (not ignored)
$paths  = git diff --name-only HEAD
$paths += git ls-files --others --exclude-standard
$paths  = $paths | Sort-Object -Unique

Write-Host ""
Write-Host "Files ≥ 95 MB (modified / new)" -ForegroundColor Cyan
Write-Host "-------------------------------------------"

$found = $false
foreach ($p in $paths) {
    if (Test-Path $p) {
        $size = (Get-Item $p).Length
        if ($size -ge $Threshold) {
            "{0,-60} {1,8:N1} MB" -f $p, ($size/1MB)
            $found = $true
        }
    }
}

if (-not $found) { Write-Host "None." }
