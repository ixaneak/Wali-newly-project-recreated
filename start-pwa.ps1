# Wali Development Environment - Quick Start

Write-Host "🚀 Starting Wali Development Environment..." -ForegroundColor Green

$ErrorActionPreference = "Stop"

# Check if we're in the right directory
if (-not (Test-Path "wali-pwa")) {
    Write-Host "❌ Error: Please run this script from the wali-backend directory" -ForegroundColor Red
    exit 1
}

# 1. Start Web PWA
Write-Host "`n📱 Starting Web PWA..." -ForegroundColor Cyan
cd wali-pwa

# Check if node_modules exists
if (-not (Test-Path "node_modules")) {
    Write-Host "📦 Installing dependencies..." -ForegroundColor Yellow
    npm install
}

# Check if .env.local exists
if (-not (Test-Path ".env.local")) {
    Write-Host "📝 Creating environment file..." -ForegroundColor Yellow
    Copy-Item ".env.local.example" ".env.local"
}

Write-Host "🌐 Starting Next.js on http://localhost:3000" -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; npm run dev"

cd ..

Write-Host "`n✅ Services starting..." -ForegroundColor Green
Write-Host "`nAccess the PWA at: http://localhost:3000" -ForegroundColor Cyan
Write-Host "`nPress Ctrl+C in the opened windows to stop services" -ForegroundColor Yellow
