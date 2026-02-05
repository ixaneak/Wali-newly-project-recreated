
# Valid JWT Token (HS256 with dev-secret)
# Generated using a helper script or hardcoded for dev-secret, matching verify-payment-flow.ps1 Logic

function Get-TestJWT {
    $header = [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes('{"alg":"HS256","typ":"JWT"}')).Trim('=').Replace('+', '-').Replace('/', '_')
    $ts = [int][double]::Parse((Get-Date -UFormat %s))
    $exp = $ts + 3600
    # PowerShell 5.1 safe timestamp
    $ts = [int64](([DateTime]::UtcNow - [DateTime]::new(1970, 1, 1)).TotalSeconds)
    $exp = $ts + 3600
    $payloadJson = "{""sub"":""test-user-rate-limit"",""role"":""user"",""iat"":$ts,""exp"":$exp}"
    
    $payload = [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($payloadJson)).Trim('=').Replace('+', '-').Replace('/', '_')
    
    $secret = "dev-secret"
    $hmac = New-Object System.Security.Cryptography.HMACSHA256
    $hmac.Key = [System.Text.Encoding]::UTF8.GetBytes($secret)
    $signature = $hmac.ComputeHash([System.Text.Encoding]::UTF8.GetBytes("$header.$payload"))
    $sigBase64 = [Convert]::ToBase64String($signature).Trim('=').Replace('+', '-').Replace('/', '_')
    
    return "$header.$payload.$sigBase64"
}

$token = Get-TestJWT
$headers = @{
    "Authorization" = "Bearer $token"
    "Content-Type"  = "application/json"
}

$body = @{
    "amount"    = 100
    "currency"  = "XOF"
    "provider"  = "orange"
    "phone"     = "+2250707070707"
    "policy_id" = "test-policy"
} | ConvertTo-Json


Write-Host "🚀 Starting Rate Limit Test..."
Write-Host "Sending 10 requests rapidly (Limit should be 5)..."

for ($i = 1; $i -le 10; $i++) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8080/api/v1/payments/initiate" -Method Post -Headers $headers -Body $body -UseBasicParsing -ErrorAction Stop
        
        # In PS, headers might be a dictionary
        $remaining = $response.Headers["X-RateLimit-Remaining"]
        if ($null -eq $remaining) { $remaining = "Unknown" }
        
        Write-Host ("Request " + $i + ": 200 OK (Remaining: " + $remaining + ")")
    }
    catch {
        # $_.Exception.Response is the WebResponse
        if ($_.Exception.Response.StatusCode -eq [System.Net.HttpStatusCode]::TooManyRequests) {
            Write-Host ("Request " + $i + ": 429 Too Many Requests (SUCCESS)") -ForegroundColor Green
            
            $h = $_.Exception.Response.Headers
            Write-Host ("Limit: " + $h["X-RateLimit-Limit"])
            Write-Host ("Remaining: " + $h["X-RateLimit-Remaining"])
            Write-Host ("Reset: " + $h["X-RateLimit-Reset"])
        }
        else {
            Write-Host ("Request " + $i + ": Error " + $_.Exception.Message) -ForegroundColor Red
        }
    }
}
