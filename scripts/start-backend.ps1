# Start backend in development mode
param(
    [int]$Port = 8000
)

Write-Host "Activating virtualenv and starting backend on port $Port"
$venv = Join-Path $PSScriptRoot "..\backend\.venv\Scripts\Activate.ps1"
if (Test-Path $venv) {
    & $venv
}
else {
    Write-Host "Virtualenv activate script not found. Create venv with: python -m venv backend/.venv"
}

Set-Location (Join-Path $PSScriptRoot "..\backend")
uvicorn app.main:app --reload --host 0.0.0.0 --port $Port
