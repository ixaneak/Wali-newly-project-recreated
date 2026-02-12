
# Wali Backend - Mock Mode Startup Script
# Starts Policy, Claims, and Payment services with mock databases and providers.

Write-Host "🚀 Starting Wali Backend in MOCK MODE..." -ForegroundColor Green
$ErrorActionPreference = "Stop"

# 1. Policy Service (Port 8000)
Write-Host "Starting Policy Service (Port 8000)..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd python-services/policy-service; `$env:USE_MOCK_DB='True'; `$env:JWT_SECRET='dev-secret'; `$env:IS_SAAS_PLATFORM='True'; `$env:NAF_CODE='6201Z'; `$env:UNDERWRITING_PARTNER='NSIA'; python -m uvicorn app.main:app --reload --port 8000"

# 2. Claims Service (Port 8001)
Write-Host "Starting Claims Service (Port 8001)..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd python-services/claims-service; `$env:USE_MOCK_DB='True'; `$env:JWT_SECRET='dev-secret'; `$env:IS_SAAS_PLATFORM='True'; python -m uvicorn app.main:app --reload --port 8001"

# 3. Compliance Service (Port 8002)
Write-Host "Starting Compliance Service (Port 8002)..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd python-services/compliance-service; `$env:DATABASE_URL='sqlite:///./test.db'; `$env:IS_SAAS_PLATFORM='True'; python -m uvicorn app.main:app --reload --port 8002"

# 4. Notification Service (Port 8003)
Write-Host "Starting Notification Service (Port 8003)..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd typescript-apps/notification-service; npm run dev"

# 5. Payment Service (Port 8080 - Go)
Write-Host "Starting Payment Service (Port 8080)..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd go-services/payment-service; `$env:PORT='8080'; `$env:MOCK_PAYMENT_PROVIDERS='true'; go run main.go"

Write-Host "`n✅ All Backend Services Started in Mock Mode" -ForegroundColor Green
Write-Host "Policy Service: http://localhost:8000"
Write-Host "Claims Service: http://localhost:8001"
Write-Host "Compliance Service: http://localhost:8002"
Write-Host "Notification Service: http://localhost:8003"
Write-Host "Payment Service: http://localhost:8080"
Write-Host "`nPress any key to exit this launcher (services will keep running in new windows)..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
