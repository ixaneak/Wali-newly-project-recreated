# Verify Backend Payment Flow Integration (Authenticated)
$ErrorActionPreference = "Stop"
$JWT_SECRET = "dev-secret"

# ==================== JWT Helper ====================
function ConvertTo-Base64UrlString($Bytes) {
    [Convert]::ToBase64String($Bytes).Trim("=").Replace("+", "-").Replace("/", "_")
}

function Create-Jwt {
    param($Secret, $Sub)
    
    $Header = @{ alg = "HS256"; typ = "JWT" }
    $Exp = [int](Get-Date).AddHours(1).ToUniversalTime().Subtract([datetime]"1970-01-01").TotalSeconds
    $Payload = @{ sub = $Sub; exp = $Exp }
    
    $HeaderJson = $Header | ConvertTo-Json -Compress
    $PayloadJson = $Payload | ConvertTo-Json -Compress
    
    $HeaderBytes = [System.Text.Encoding]::UTF8.GetBytes($HeaderJson)
    $PayloadBytes = [System.Text.Encoding]::UTF8.GetBytes($PayloadJson)
    
    $HeaderCal = ConvertTo-Base64UrlString $HeaderBytes
    $PayloadCal = ConvertTo-Base64UrlString $PayloadBytes
    
    $SignatureInput = "$HeaderCal.$PayloadCal"
    $Key = [System.Text.Encoding]::UTF8.GetBytes($Secret)
    $HMAC = New-Object System.Security.Cryptography.HMACSHA256(, $Key)
    $SignatureBytes = $HMAC.ComputeHash([System.Text.Encoding]::UTF8.GetBytes($SignatureInput))
    $SignatureCal = ConvertTo-Base64UrlString $SignatureBytes
    
    return "$HeaderCal.$PayloadCal.$SignatureCal"
}
# ====================================================

function Test-Endpoint($Name, $Uri, $Method, $Body) {
    Write-Host "Testing $Name..." -NoNewline
    $Token = Create-Jwt -Secret $JWT_SECRET -Sub "test-user-verify-1"
    $Headers = @{ Authorization = "Bearer $Token" }
    
    try {
        if ($Body) {
            $Response = Invoke-RestMethod -Uri $Uri -Method $Method -Headers $Headers -Body ($Body | ConvertTo-Json -Depth 5) -ContentType "application/json"
        }
        else {
            $Response = Invoke-RestMethod -Uri $Uri -Method $Method -Headers $Headers
        }
        Write-Host " ✅ OK" -ForegroundColor Green
        return $Response
    }
    catch {
        Write-Host " ❌ FAILED" -ForegroundColor Red
        Write-Host $_.Exception.Message
        if ($_.Exception.Response) {
            $Stream = $_.Exception.Response.GetResponseStream()
            $Reader = New-Object System.IO.StreamReader($Stream)
            Write-Host $Reader.ReadToEnd()
        }
        exit 1
    }
}

# 1. Create Policy (Policy Service :8000)
$PolicyBody = @{
    user_id           = "test-user-verify-1"
    coverage_type     = "health"
    coverage_details  = @{
        max_coverage_amount = 1000000
        description         = "Verification Plan"
    }
    payment_frequency = "monthly"
    region            = "Abidjan"
}
$Policy = Test-Endpoint "Create Policy" "http://localhost:8000/api/v1/policies/" "POST" $PolicyBody
$PolicyID = $Policy.id
Write-Host "-> Created Policy ID: $PolicyID" -ForegroundColor Gray

# 2. Initiate Payment (Payment Service :8080)
$PaymentBody = @{
    user_id         = "test-user-verify-1"
    policy_id       = $PolicyID
    amount          = 15000
    phone           = "+22507070707"
    provider        = "orange"
    idempotency_key = [Guid]::NewGuid().ToString()
}
$Payment = Test-Endpoint "Initiate Payment" "http://localhost:8080/api/v1/payments/initiate" "POST" $PaymentBody
$TransactionRef = $Payment.transaction_ref
Write-Host "-> Transaction Ref: $TransactionRef" -ForegroundColor Gray

# 3. Simulate Orange Webhook (Payment Service :8080)
# (Same secret used to sign mock webhook? Or provider doesn't check JWT?
# The webhook endpoint handlers usually verify signatures, but for Orange it might be open or different.
# payment.go handler: OrangeWebhook doesn't seem to check signature yet, just binds JSON.
# And endpoints /webhooks/... are usually PUBLIC or check signature, NOT JWT.
# In `main.go`, `webhooks` group is OUTSIDE `api.Use(middleware.JWTAuthMiddleware())`?
# Let's check `main.go` view.
# line 96: `webhooks := router.Group("/webhooks")`. No middleware usage shown *on this group*.
# line 85: `api := router.Group("/api/v1")`. `api.Use(...)`.
# So webhooks are likely public (no JWT needed).)

function Test-Webhook($Name, $Uri, $Method, $Body) {
    Write-Host "Testing $Name..." -NoNewline
    try {
        $Response = Invoke-RestMethod -Uri $Uri -Method $Method -Body ($Body | ConvertTo-Json -Depth 5) -ContentType "application/json"
        Write-Host " ✅ OK" -ForegroundColor Green
        return $Response
    }
    catch {
        Write-Host " ❌ FAILED" -ForegroundColor Red
        Write-Host $_.Exception.Message
        exit 1
    }
}

$WebhookBody = @{
    status         = "SUCCESS"
    transaction_id = "orange-tx-123"
    reference      = $TransactionRef
    amount         = 15000
    currency       = "XOF"
}
Test-Webhook "Simulate Webhook" "http://localhost:8080/webhooks/orange/payments" "POST" $WebhookBody

# 4. Verify Policy Activation (Policy Service :8000)
# We wait a moment as activation is async in the webhook handler (goroutine)
Start-Sleep -Seconds 3

$UpdatedPolicy = Test-Endpoint "Check Policy Status" "http://localhost:8000/api/v1/policies/$PolicyID" "GET" $null
$Status = $UpdatedPolicy.status

if ($Status -eq "active") {
    Write-Host "✅ SUCCESS: Policy status is '$Status'" -ForegroundColor Green
}
else {
    Write-Host "❌ FAILURE: Policy status is '$Status' (expected 'active')" -ForegroundColor Red
    exit 1
}
