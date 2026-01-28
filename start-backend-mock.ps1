
# Wali Backend - Mock Mode Startup Script
# Starts Policy, Claims, and Payment services with mock databases and providers.

Write-Host "🚀 Starting Wali Backend in MOCK MODE..." -ForegroundColor Green
$ErrorActionPreference = "Stop"

# 1. Policy Service (Port 8000)
Write-Host "Starting Policy Service (Port 8000)..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd services/policy-service; `$env:USE_MOCK_DB='True'; `$env:JWT_SECRET='dev-secret'; `$env:ESCROW_BANK_ACCOUNT='123'; `$env:OPERATING_BANK_ACCOUNT='456'; uvicorn app.main:app --reload --port 8000"

# 2. Claims Service (Port 8001)
Write-Host "Starting Claims Service (Port 8001)..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd services/claims-service; `$env:USE_MOCK_DB='True'; `$env:JWT_SECRET='dev-secret'; uvicorn app.main:app --reload --port 8001"

# 3. Payment Service (Port 8082 - Go)
Write-Host "Starting Payment Service (Port 8082)..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd services/payment-service; `$env:PORT='8082'; `$env:MOCK_PAYMENT_PROVIDERS='true'; go run main.go"

Write-Host "`n✅ All Backend Services Started in Mock Mode" -ForegroundColor Green
Write-Host "Policy Service: http://localhost:8000"
Write-Host "Claims Service: http://localhost:8001"
Write-Host "Payment Service: http://localhost:8082"
Write-Host "`nPress any key to exit this launcher (services will keep running in new windows)..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
