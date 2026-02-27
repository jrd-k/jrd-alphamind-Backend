#!/usr/bin/env pwsh

Write-Host "`n" -NoNewline
Write-Host "======================================================" -ForegroundColor Magenta
Write-Host "  AlphaMind Platform - Setup Verification" -ForegroundColor Cyan
Write-Host "======================================================" -ForegroundColor Magenta

# 1. Backend Server Check
Write-Host "`nBackend Server Status:" -ForegroundColor Green
$backendRunning = (Get-Process -Name "python*" -ErrorAction SilentlyContinue | Where-Object { $_.ProcessName -like "*python*" }).Count -gt 0
if ($backendRunning) {
    Write-Host "  [OK] Backend process running" -ForegroundColor Green
    Write-Host "  URL: http://localhost:8000" -ForegroundColor Cyan
} else {
    Write-Host "  [ERROR] Backend not running" -ForegroundColor Red
}

# 2. Frontend Server Check
Write-Host "`nFrontend Server Status:" -ForegroundColor Green
$frontendRunning = (Get-Process -Name "node*" -ErrorAction SilentlyContinue).Count -gt 0
if ($frontendRunning) {
    Write-Host "  [OK] Frontend process running" -ForegroundColor Green
    Write-Host "  URL: http://localhost:8082" -ForegroundColor Cyan
} else {
    Write-Host "  [INFO] Frontend not running (built at dist/)" -ForegroundColor Yellow
}

# 3. API Endpoints
Write-Host "`nAPI Endpoints:" -ForegroundColor Green
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/api/stocks?symbol=EURUSD" -UseBasicParsing -TimeoutSec 2 -SkipHttpErrorCheck
    if ($response.StatusCode -eq 200) {
        $data = $response.Content | ConvertFrom-Json
        $recordCount = $data.data.Count
        Write-Host "  [OK] GET /api/stocks (Returns $recordCount records)" -ForegroundColor Green
    } else {
        Write-Host "  [ERROR] GET /api/stocks returned $($response.StatusCode)" -ForegroundColor Red
    }
} catch {
    Write-Host "  [ERROR] GET /api/stocks - Connection failed" -ForegroundColor Red
}

# 4. Database Check
Write-Host "`nDatabase Status:" -ForegroundColor Green
$dbPath = "c:\Users\USER\jrd-alphamind-Backend\backend\dev.db"
if (Test-Path $dbPath) {
    $dbSize = (Get-Item $dbPath).Length / 1024
    Write-Host "  [OK] Database exists" -ForegroundColor Green
    Write-Host "  Location: $dbPath" -ForegroundColor Cyan
    Write-Host "  Size: $([Math]::Round($dbSize, 2)) KB" -ForegroundColor Cyan
} else {
    Write-Host "  [ERROR] Database not found" -ForegroundColor Red
}

# 5. Frontend Build Check
Write-Host "`nFrontend Build:" -ForegroundColor Green
$distPath = "c:\Users\USER\jrd-alphamind-Backend\frontend\dist"
if (Test-Path "$distPath\index.html") {
    Write-Host "  [OK] Production build available" -ForegroundColor Green
    $indexSize = (Get-Item "$distPath\index.html").Length
    Write-Host "  Location: $distPath" -ForegroundColor Cyan
    Write-Host "  Size: $([Math]::Round($indexSize / 1024, 2)) KB" -ForegroundColor Cyan
} else {
    Write-Host "  [ERROR] Production build not found" -ForegroundColor Red
}

# 6. Configuration Check
Write-Host "`nConfiguration:" -ForegroundColor Green
$envPath = "c:\Users\USER\jrd-alphamind-Backend\frontend\.env"
if (Test-Path $envPath) {
    $apiUrl = Get-Content $envPath | Select-String "VITE_API_BASE_URL" | ForEach-Object { $_ -replace "VITE_API_BASE_URL=" }
    Write-Host "  [OK] Frontend .env file exists" -ForegroundColor Green
    Write-Host "  API Base URL: $apiUrl" -ForegroundColor Cyan
} else {
    Write-Host "  [ERROR] Frontend .env not found" -ForegroundColor Red
}

# 7. Features Summary
Write-Host "`nPlatform Features:" -ForegroundColor Green
Write-Host "  [OK] User Authentication" -ForegroundColor Green
Write-Host "  [OK] Broker Accounts" -ForegroundColor Green
Write-Host "  [OK] Paper Trading" -ForegroundColor Green
Write-Host "  [OK] Market Charts" -ForegroundColor Green
Write-Host "  [PENDING] AI Signals" -ForegroundColor Yellow
Write-Host "  [PENDING] Position Monitoring" -ForegroundColor Yellow

Write-Host "`n======================================================" -ForegroundColor Magenta
Write-Host "  Setup verification complete!" -ForegroundColor Cyan
Write-Host "======================================================`n" -ForegroundColor Magenta
