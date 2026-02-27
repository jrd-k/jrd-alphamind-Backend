# Start frontend dev server (Vite)
Write-Host "Starting frontend dev server (Vite) on port 8081"
Set-Location (Join-Path $PSScriptRoot "..\frontend")
if (Test-Path "node_modules") {
    npm run dev
} else {
    Write-Host "node_modules not found. Run: npm install"
}
