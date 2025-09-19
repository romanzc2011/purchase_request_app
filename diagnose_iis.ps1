# IIS Configuration Diagnostic Script
Write-Host "=== IIS Configuration Diagnostic ===" -ForegroundColor Green

# Check if the deployment path exists
$deploymentPath = "C:\Users\romancampbell\source\deployments\pras\dist"
Write-Host "Checking deployment path: $deploymentPath" -ForegroundColor Yellow

if (Test-Path $deploymentPath) {
    Write-Host "✅ Deployment path exists" -ForegroundColor Green
    
    # Check if web.config exists in deployment path
    $webConfigPath = Join-Path $deploymentPath "web.config"
    if (Test-Path $webConfigPath) {
        Write-Host "✅ web.config exists in deployment path" -ForegroundColor Green
        
        # Validate XML syntax
        try {
            [xml]$config = Get-Content $webConfigPath
            Write-Host "✅ web.config XML syntax is valid" -ForegroundColor Green
        }
        catch {
            Write-Host "❌ web.config XML syntax error: $($_.Exception.Message)" -ForegroundColor Red
        }
    }
    else {
        Write-Host "❌ web.config not found in deployment path" -ForegroundColor Red
        Write-Host "Copying web.config to deployment path..." -ForegroundColor Yellow
        Copy-Item "web.config" $webConfigPath -Force
    }
}
else {
    Write-Host "❌ Deployment path does not exist" -ForegroundColor Red
    Write-Host "Creating deployment path..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $deploymentPath -Force
    Copy-Item "web.config" (Join-Path $deploymentPath "web.config") -Force
}

# Check if URL Rewrite Module is installed
Write-Host "`nChecking URL Rewrite Module..." -ForegroundColor Yellow
$rewriteModule = Get-WindowsFeature -Name "IIS-HttpRedirect" -ErrorAction SilentlyContinue
if ($rewriteModule -and $rewriteModule.InstallState -eq "Installed") {
    Write-Host "✅ URL Rewrite Module is installed" -ForegroundColor Green
}
else {
    Write-Host "❌ URL Rewrite Module may not be installed" -ForegroundColor Red
    Write-Host "Please install URL Rewrite Module from: https://www.iis.net/downloads/microsoft/url-rewrite" -ForegroundColor Yellow
}

# Check if WebSocket feature is enabled
Write-Host "`nChecking WebSocket support..." -ForegroundColor Yellow
$websocketFeature = Get-WindowsFeature -Name "IIS-WebSockets" -ErrorAction SilentlyContinue
if ($websocketFeature -and $websocketFeature.InstallState -eq "Installed") {
    Write-Host "✅ WebSocket feature is enabled" -ForegroundColor Green
}
else {
    Write-Host "❌ WebSocket feature may not be enabled" -ForegroundColor Red
    Write-Host "Please enable WebSocket feature in IIS" -ForegroundColor Yellow
}

# Check if backend server is running
Write-Host "`nChecking backend server..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://127.0.0.1:5004/api/test-socketio" -TimeoutSec 5 -ErrorAction Stop
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ Backend server is running and accessible" -ForegroundColor Green
    }
}
catch {
    Write-Host "❌ Backend server is not accessible: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Please start your backend server on port 5004" -ForegroundColor Yellow
}

Write-Host "`n=== Diagnostic Complete ===" -ForegroundColor Green
