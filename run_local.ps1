<#
Run TopNum locally using the vendored or in-repo `nba_api` package.

Options:
 - If you ran `copy_vendor.ps1`, this script will prefer `tools\topnum\vendor` as PYTHONPATH.
 - Otherwise set PYTHONPATH to the repository `src` manually.

Usage:
  From the repository root (PowerShell):
    .\tools\topnum\run_local.ps1
#>

$repo = Get-Location
$vendor = Join-Path $repo 'tools\topnum\vendor'

if (Test-Path (Join-Path $vendor 'nba_api')) {
    Write-Host "Using vendored nba_api in $vendor"
    $env:PYTHONPATH = $vendor
} else {
    Write-Host "Vendored package not found. Using repository src as PYTHONPATH."
    $env:PYTHONPATH = Join-Path $repo 'src'
}

Write-Host "Starting Streamlit (press Ctrl+C to stop)..."
$pythonExe = $env:PYTHON_EXE
if (-not $pythonExe) {
    $venvPy = Join-Path $repo '.venv\Scripts\python.exe'
    if (Test-Path $venvPy) { $pythonExe = $venvPy }
}
if (-not $pythonExe) { $pythonExe = 'python' }
& $pythonExe -m streamlit run tools/topnum/app.py
