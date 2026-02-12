# Check for forbidden insurance keywords identifying non-SaaS activity
$ErrorActionPreference = "Stop"

$ForbiddenTerms = @(
    "premium_collected", 
    "calculate_premium", 
    "PremiumCalculator", 
    "escrow", 
    "hold_funds", 
    "commission_earned", 
    "broker_fee"
)

$PathToScan = "python-services/policy-service"
$Errors = 0

Write-Host "Scanning for non-compliant Insurance terminology..." -ForegroundColor Cyan

if (Test-Path $PathToScan) {
    foreach ($term in $ForbiddenTerms) {
        $foundLines = Get-ChildItem -Path $PathToScan -Recurse -Include *.py | Where-Object { $_.FullName -notlike "*alembic*" -and $_.Name -ne "test_saas_compliance.py" } | Select-String -Pattern $term
        if ($foundLines) {
            Write-Host "VIOLATION: Found forbidden term '$term'" -ForegroundColor Red
            foreach ($match in $foundLines) {
                Write-Host "   File: $($match.Path)"
                Write-Host "   Line: $($match.LineNumber): $($match.Line.Trim())"
            }
            $Errors++
        }
    }
}

# Check for required SaaS flags
$ConfigPath = "$PathToScan/app/config/compliance.py"
if (Test-Path $ConfigPath) {
    $saasFlag = Select-String -Path $ConfigPath -Pattern "IS_SAAS_PLATFORM.*=.*True"
    if (-not $saasFlag) {
        Write-Host "VIOLATION: 'IS_SAAS_PLATFORM = True' not found in $ConfigPath" -ForegroundColor Red
        $Errors++
    }
}
else {
    Write-Host "WARNING: Config file not found: $ConfigPath" -ForegroundColor Yellow
}

if ($Errors -eq 0) {
    Write-Host "COMPLIANCE PASSED: Codebase operates as Technology Provider." -ForegroundColor Green
    exit 0
}
else {
    Write-Host "COMPLIANCE FAILED: $Errors violations found." -ForegroundColor Red
    exit 1
}
