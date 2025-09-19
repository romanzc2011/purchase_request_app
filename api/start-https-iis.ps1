# Start the backend with HTTPS using existing IIS certificates
# This script exports certificates from IIS and starts the backend with HTTPS

Write-Host "🔐 Using existing IIS certificates for HTTPS..."

# Check if certificates exist in the store
$certificates = Get-ChildItem Cert:\LocalMachine\My | Where-Object { $_.Subject -like "*localhost*" -or $_.Subject -like "*LAWB-SHCOL-7920*" }

if ($certificates.Count -eq 0) {
    Write-Host "❌ No suitable certificates found in LocalMachine\My store"
    Write-Host "   Available certificates:"
    Get-ChildItem Cert:\LocalMachine\My | Select-Object Subject, Thumbprint
    exit 1
}

# Use the first suitable certificate
$cert = $certificates[0]
Write-Host "✅ Using certificate: $($cert.Subject)"

# Create tls_certs directory if it doesn't exist
if (-not (Test-Path "tls_certs")) {
    New-Item -ItemType Directory -Path "tls_certs" | Out-Null
}

# Export certificate to files
$certPath = "tls_certs/server.crt"
$keyPath = "tls_certs/server.key"

try {
    # Export certificate
    $certBytes = $cert.Export([System.Security.Cryptography.X509Certificates.X509ContentType]::Cert)
    [System.IO.File]::WriteAllBytes($certPath, $certBytes)
    
    # Export private key (this requires the certificate to have an exportable private key)
    $keyBytes = $cert.PrivateKey.ExportPkcs8PrivateKey()
    [System.IO.File]::WriteAllBytes($keyPath, $keyBytes)
    
    Write-Host "✅ Certificate exported to: $certPath"
    Write-Host "✅ Private key exported to: $keyPath"
    
} catch {
    Write-Host "❌ Error exporting certificate: $($_.Exception.Message)"
    Write-Host "   The certificate may not have an exportable private key."
    Write-Host "   Try running as Administrator or use a different certificate."
    exit 1
}

# Start the backend with HTTPS
Write-Host "🚀 Starting PRAS API with HTTPS using IIS certificate..."
python -m uvicorn api.pras_api:app --host 0.0.0.0 --port 5004 --ssl-keyfile tls_certs/server.key --ssl-certfile tls_certs/server.crt --reload

Write-Host "✅ Backend started with HTTPS at https://localhost:5004"
