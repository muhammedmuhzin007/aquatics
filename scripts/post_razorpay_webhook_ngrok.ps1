<#
post_razorpay_webhook_ngrok.ps1

Starts ngrok (if available), discovers the public HTTPS tunnel, computes a
Razorpay-style HMAC SHA256 signature for a minimal `payment.captured` webhook
body using `RAZORPAY_WEBHOOK_SECRET` from `.env`, posts the webhook to the
local endpoint exposed via ngrok, and prints the response.

Usage (PowerShell):
  cd <project-root-containing-manage.py>
  .\aquatics\scripts\post_razorpay_webhook_ngrok.ps1

Optional parameters:
  -OrderId <int>         Internal Order.id to include in simulated payload (default: 1)
  -ProviderOrderId <str> Provider order id (default: simulated)
  -PaymentId <str>       Payment id to simulate (default: generated)
  -Port <int>            Local port where Django is running (default: 8000)
  -NoNgrok              Do not start ngrok; use existing ngrok tunnel or set -NgrokUrl
  -NgrokUrl <str>       Use this ngrok HTTPS URL instead of starting ngrok

Notes:
 - Requires ngrok on PATH for automatic tunnel start (optional).
 - Requires your dev server to be running (python manage.py runserver).
 - The script attempts to read `RAZORPAY_WEBHOOK_SECRET` from `.env` in the
   current folder or `./aquatics/.env`.
#>

param(
    [int]$OrderId = 1,
    [string]$ProviderOrderId = "",
    [string]$PaymentId = "",
    [int]$Port = 8000,
    [switch]$NoNgrok,
    [string]$NgrokUrl = "",
    [int]$NgrokApiPort = 4040
)

Set-StrictMode -Version Latest

function Read-EnvValue {
    param([string]$Key)
    $paths = @(".env", "./aquatics/.env")
    foreach ($p in $paths) {
        if (Test-Path $p) {
            $lines = Get-Content $p -ErrorAction SilentlyContinue
            foreach ($l in $lines) {
                if ($l -match "^\s*${Key}\s*=\s*(.*)$") {
                    return $Matches[1].Trim()
                }
            }
        }
    }
    return $null
}

function Start-NgrokAndGetUrl {
    param([int]$Port, [int]$ApiPort)
    $ngrokCmd = Get-Command ngrok -ErrorAction SilentlyContinue
    if (-not $ngrokCmd) {
        Write-Host "ngrok not found on PATH. Install ngrok or provide -NgrokUrl." -ForegroundColor Yellow
        return $null
    }

    # Start ngrok in a hidden window and capture the process
    $startInfo = @{FilePath = $ngrokCmd.Path; ArgumentList = @('http', $Port); WindowStyle='Hidden'}
    $proc = Start-Process @startInfo -PassThru
    Write-Host "Started ngrok (PID $($proc.Id)). Waiting for tunnel to appear..."

    $apiUrl = "http://127.0.0.1:$ApiPort/api/tunnels"
    $attempts = 0
    while ($attempts -lt 30) {
        Start-Sleep -Seconds 1
        try {
            $resp = Invoke-RestMethod -Uri $apiUrl -Method Get -ErrorAction Stop
            if ($resp.tunnels) {
                foreach ($t in $resp.tunnels) {
                    if ($t.public_url -like 'https://*') {
                        return @{ Url = $t.public_url; Process = $proc }
                    }
                }
            }
        } catch {
            # Continue waiting
        }
        $attempts++
    }
    Write-Host "Timed out waiting for ngrok tunnel (checked $attempts times)." -ForegroundColor Red
    return $null
}

function Compute-HmacHex {
    param([string]$Secret, [byte[]]$BodyBytes)
    $key = [System.Text.Encoding]::UTF8.GetBytes($Secret)
    $hmac = New-Object System.Security.Cryptography.HMACSHA256($key)
    $hash = $hmac.ComputeHash($BodyBytes)
    # return lowercase hex
    return ([System.BitConverter]::ToString($hash) -replace '-', '').ToLower()
}

try {
    # Determine webhook secret
    $webhookSecret = Read-EnvValue -Key 'RAZORPAY_WEBHOOK_SECRET'
    if (-not $webhookSecret) {
        Write-Host "RAZORPAY_WEBHOOK_SECRET not found in .env. Please set it." -ForegroundColor Red
        exit 1
    }

    if (-not $NgrokUrl -and -not $NoNgrok) {
        $ngrokInfo = Start-NgrokAndGetUrl -Port $Port -ApiPort $NgrokApiPort
        if ($ngrokInfo -eq $null) { exit 2 }
        $NgrokUrl = $ngrokInfo.Url
        $ngrokProc = $ngrokInfo.Process
        Write-Host "ngrok public URL: $NgrokUrl"
    } elseif ($NgrokUrl) {
        Write-Host "Using provided ngrok URL: $NgrokUrl"
    } else {
        Write-Host "Not starting ngrok (NoNgrok set). You must provide -NgrokUrl pointing at your tunnel." -ForegroundColor Yellow
    }

    if (-not $ProviderOrderId -or $ProviderOrderId -eq "") {
        $ProviderOrderId = "test_rp_order_$([guid]::NewGuid().ToString('N').Substring(0,10))"
    }
    if (-not $PaymentId -or $PaymentId -eq "") {
        $PaymentId = "pay_$([guid]::NewGuid().ToString('N').Substring(0,12))"
    }

    # Build minimal webhook JSON (payment.captured)
    $bodyObj = @{
        event = 'payment.captured'
        payload = @{
            payment = @{
                entity = @{
                    id = $PaymentId
                    order_id = $ProviderOrderId
                    amount = 1000
                }
            }
        }
    }
    $bodyJson = (ConvertTo-Json $bodyObj -Depth 10)
    $bodyBytes = [System.Text.Encoding]::UTF8.GetBytes($bodyJson)

    # Compute signature
    $signature = Compute-HmacHex -Secret $webhookSecret -BodyBytes $bodyBytes
    Write-Host "Computed signature: $signature"

    if (-not $NgrokUrl) {
        Write-Host "No ngrok URL available; cannot POST webhook." -ForegroundColor Red
        exit 3
    }

    $webhookEndpoint = "$NgrokUrl/payments/razorpay/webhook/"
    Write-Host "Posting simulated webhook to: $webhookEndpoint"

    try {
        $resp = Invoke-RestMethod -Uri $webhookEndpoint -Method Post -Body $bodyJson -ContentType 'application/json' -Headers @{ 'X-Razorpay-Signature' = $signature }
        Write-Host "Webhook POST response (object):" -ForegroundColor Green
        $resp | ConvertTo-Json -Depth 5 | Write-Host
    } catch {
        Write-Host "Invoke-RestMethod failed: $_" -ForegroundColor Red
        # Try raw web request to capture status
        try {
            $webReq = [System.Net.WebRequest]::Create($webhookEndpoint)
            $webReq.Method = 'POST'
            $webReq.ContentType = 'application/json'
            $webReq.Headers.Add('X-Razorpay-Signature', $signature)
            $bytes = $bodyBytes
            $webReq.ContentLength = $bytes.Length
            $reqStream = $webReq.GetRequestStream()
            $reqStream.Write($bytes,0,$bytes.Length)
            $reqStream.Close()
            $webResp = $webReq.GetResponse()
            $status = $webResp.StatusCode
            Write-Host "Webhook POST status: $status" -ForegroundColor Green
        } catch {
            Write-Host "Failed to POST webhook: $_" -ForegroundColor Red
        }
    }

    Write-Host "Done. If ngrok was started by this script, it will continue running in background (PID $($ngrokProc.Id))." -ForegroundColor Cyan

} catch {
    Write-Host "Error: $_" -ForegroundColor Red
    exit 10
}
