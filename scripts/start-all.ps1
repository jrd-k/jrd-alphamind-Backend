# Starts backend and frontend in separate consoles (PowerShell)
Write-Host "Starting backend and frontend"

Start-Process powershell -ArgumentList "-NoExit -Command `"& '$PSScriptRoot\start-backend.ps1'`""
Start-Process powershell -ArgumentList "-NoExit -Command `"& '$PSScriptRoot\start-frontend.ps1'`""
