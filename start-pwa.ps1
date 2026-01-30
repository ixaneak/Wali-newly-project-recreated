# Wali Development Environment - Quick Start

Write-Host "Starting Wali Development Environment..." -ForegroundColor Green

$ErrorActionPreference = "Stop"

# 1. Start Web PWA
Write-Host "Starting Web PWA..." -ForegroundColor Cyan

# Check if node_modules exists
if (-not (Test-Path "wali-pwa/node_modules")) {
    Write-Host "Installing dependencies..." -ForegroundColor Yellow
    Set-Location wali-pwa
    npm install
    Set-Location ..
}

# Check if .env.local exists
if (-not (Test-Path "wali-pwa/.env.local")) {
    Write-Host "Creating environment file..." -ForegroundColor Yellow
    Copy-Item "wali-pwa/.env.local.example" "wali-pwa/.env.local"
}

Write-Host "Starting Next.js on http://localhost:3000" -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd wali-pwa; npm run dev"

Write-Host "Services starting..." -ForegroundColor Green
Write-Host "Access the PWA at: http://localhost:3000" -ForegroundColor Cyan
Write-Host "Press Ctrl+C in the opened windows to stop services" -ForegroundColor Yellow
