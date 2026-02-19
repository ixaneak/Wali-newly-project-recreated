<#
.SYNOPSIS
    Wali PWA — Local Mobile Test Environment
.DESCRIPTION
    Starts all backend services and the PWA dev server bound to 0.0.0.0,
    so a phone on the same Wi-Fi can access the app.
    
    Usage: .\start-mobile-test.ps1
           .\start-mobile-test.ps1 -HttpsMode   # enable HTTPS via Next.js experimental flag
           .\start-mobile-test.ps1 -SkipBackend  # only start PWA (backends already running)
#>
param(
    [switch]$HttpsMode,
    [switch]$SkipBackend
)

$ErrorActionPreference = "Continue"
$ROOT = $PSScriptRoot
$PWA_DIR = Join-Path $ROOT "typescript-apps\pwa"
$VENV_PYTHON = Join-Path $ROOT ".venv\Scripts\python.exe"

# ── Detect LAN IP ──────────────────────────────────────────────
function Get-LanIP {
    $addresses = Get-NetIPAddress -AddressFamily IPv4 -InterfaceAlias "Wi-Fi*", "Ethernet*" -ErrorAction SilentlyContinue |
    Where-Object { $_.IPAddress -notlike "127.*" -and $_.IPAddress -notlike "169.254.*" } |
    Select-Object -ExpandProperty IPAddress
    
    if (-not $addresses) {
        # Fallback: grab first non-loopback IPv4
        $addresses = (Get-NetIPAddress -AddressFamily IPv4 |
            Where-Object { $_.IPAddress -notlike "127.*" -and $_.IPAddress -notlike "169.254.*" } |
            Select-Object -First 1).IPAddress
    }

    if ($addresses -is [array]) { return $addresses[0] } else { return $addresses }
}

$LAN_IP = Get-LanIP
if (-not $LAN_IP) {
    Write-Host "ERROR: Could not detect LAN IP. Are you connected to Wi-Fi?" -ForegroundColor Red
    exit 1
}

# ── Banner ─────────────────────────────────────────────────────
Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║         Wali PWA — Mobile Test Environment          ║" -ForegroundColor Cyan
Write-Host "╠══════════════════════════════════════════════════════╣" -ForegroundColor Cyan
Write-Host "║                                                      ║" -ForegroundColor Cyan

$protocol = if ($HttpsMode) { "https" } else { "http" }
$mobileUrl = "${protocol}://${LAN_IP}:3000"

Write-Host "║  LAN IP:   $LAN_IP" -ForegroundColor Green -NoNewline
Write-Host (" " * (39 - $LAN_IP.Length)) -NoNewline
Write-Host "║" -ForegroundColor Cyan
Write-Host "║  Mobile URL: $mobileUrl" -ForegroundColor Yellow -NoNewline
Write-Host (" " * (35 - $mobileUrl.Length)) -NoNewline
Write-Host "║" -ForegroundColor Cyan
Write-Host "║                                                      ║" -ForegroundColor Cyan
Write-Host "║  Open this URL on your phone (same Wi-Fi network)   ║" -ForegroundColor White
Write-Host "║                                                      ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# ── Check Windows Firewall ─────────────────────────────────────
Write-Host "[1/4] Checking firewall rules..." -ForegroundColor DarkGray
$ruleName = "Wali-Mobile-Test"
$existingRule = Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue
if (-not $existingRule) {
    Write-Host "  Adding firewall rule for ports 3000, 8000, 8001..." -ForegroundColor Yellow
    try {
        New-NetFirewallRule -DisplayName $ruleName `
            -Direction Inbound `
            -Action Allow `
            -Protocol TCP `
            -LocalPort 3000, 8000, 8001 `
            -Profile Private `
            -Description "Allow phone to access Wali dev services on LAN" | Out-Null
        Write-Host "  Firewall rule added." -ForegroundColor Green
    }
    catch {
        Write-Host "  WARNING: Could not add firewall rule (run as Admin if needed)." -ForegroundColor Yellow
        Write-Host "  You may need to manually allow ports 3000, 8000, 8001." -ForegroundColor Yellow
    }
}
else {
    Write-Host "  Firewall rule already exists." -ForegroundColor Green
}

# ── Start Backend Services ─────────────────────────────────────
if (-not $SkipBackend) {
    Write-Host "[2/4] Starting backend services..." -ForegroundColor DarkGray

    # Policy Service (port 8000)
    $policyRunning = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
    if ($policyRunning) {
        Write-Host "  Policy Service (8000): already running" -ForegroundColor Green
    }
    else {
        Write-Host "  Starting Policy Service on port 8000..." -ForegroundColor Yellow
        $policyDir = Join-Path $ROOT "python-services\policy-service"
        Start-Process -NoNewWindow -FilePath $VENV_PYTHON -ArgumentList "-m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload" -WorkingDirectory $policyDir
        Start-Sleep -Seconds 3
        Write-Host "  Policy Service (8000): started" -ForegroundColor Green
    }

    # Claims Service (port 8001)
    $claimsRunning = Get-NetTCPConnection -LocalPort 8001 -State Listen -ErrorAction SilentlyContinue
    if ($claimsRunning) {
        Write-Host "  Claims Service (8001): already running" -ForegroundColor Green
    }
    else {
        Write-Host "  Starting Claims Service on port 8001..." -ForegroundColor Yellow
        $claimsDir = Join-Path $ROOT "python-services\claims-service"
        Start-Process -NoNewWindow -FilePath $VENV_PYTHON -ArgumentList "-m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload" -WorkingDirectory $claimsDir
        Start-Sleep -Seconds 3
        Write-Host "  Claims Service (8001): started" -ForegroundColor Green
    }
}
else {
    Write-Host "[2/4] Skipping backend (--SkipBackend flag)." -ForegroundColor DarkGray
}

# ── Health Check ───────────────────────────────────────────────
Write-Host "[3/4] Running health checks..." -ForegroundColor DarkGray
Start-Sleep -Seconds 2

$services = @(
    @{ Name = "Policy Service"; Url = "http://localhost:8000/health" },
    @{ Name = "Claims Service"; Url = "http://localhost:8001/health" }
)

foreach ($svc in $services) {
    try {
        $response = Invoke-WebRequest -Uri $svc.Url -TimeoutSec 5 -UseBasicParsing -ErrorAction Stop
        Write-Host ("  {0}: OK ({1})" -f $svc.Name, $response.StatusCode) -ForegroundColor Green
    }
    catch {
        Write-Host ("  {0}: UNAVAILABLE (non-critical)" -f $svc.Name) -ForegroundColor Yellow
    }
}

# ── Start PWA Dev Server ───────────────────────────────────────
Write-Host "[4/4] Starting PWA dev server on 0.0.0.0:3000..." -ForegroundColor DarkGray

$pwaRunning = Get-NetTCPConnection -LocalPort 3000 -State Listen -ErrorAction SilentlyContinue
if ($pwaRunning) {
    Write-Host "  PWA already running on port 3000. Kill it first if you want a fresh start." -ForegroundColor Yellow
}
else {
    $env:HOSTNAME = "0.0.0.0"

    Write-Host ""
    Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host "  Ready! Open on your phone:" -ForegroundColor White
    Write-Host "  $mobileUrl" -ForegroundColor Yellow -BackgroundColor DarkBlue
    Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host ""

    Set-Location $PWA_DIR
    if ($HttpsMode) {
        & npm run dev -- -H 0.0.0.0 --experimental-https
    }
    else {
        & npm run dev -- -H 0.0.0.0
    }
}
