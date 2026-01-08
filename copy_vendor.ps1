<#
Copy the in-repo `src\nba_api` package into this folder's `vendor\nba_api` directory.
Run this from the repository root (or adjust paths) in PowerShell.

Usage:
  .\tools\topnum\copy_vendor.ps1

This will create `tools\topnum\vendor\nba_api` containing a copy of the local nba_api package.
#>

$src = Join-Path -Path (Get-Location) -ChildPath 'src\nba_api'
$dst = Join-Path -Path (Get-Location) -ChildPath 'tools\topnum\vendor\nba_api'

Write-Host "Copying from $src to $dst"

if (-not (Test-Path $src)) {
    Write-Error "Source path not found: $src"
    exit 1
}

# Ensure destination exists
New-Item -ItemType Directory -Force -Path $dst | Out-Null

# Use Robocopy for robust copying on Windows
$robocopyArgs = @($src, $dst, '/MIR', '/NFL', '/NDL', '/NJH', '/NJS')

Write-Host "Running robocopy..."
robocopy @robocopyArgs | Out-Null

if ($LASTEXITCODE -ge 8) {
    Write-Warning "Robocopy reported a problem (exit code: $LASTEXITCODE). Check output above."
} else {
    Write-Host "Copy complete. Vendor directory created at: $dst"
}
