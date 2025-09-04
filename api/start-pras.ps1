$root = Split-Path $PSScriptRoot -Parent
$venvPy = Join-Path $PSScriptRoot 'PRAS_API\Scripts\python.exe'
New-Item -ItemType Directory -Force -Path "$root\logs" | Out-Null

# Start-Process -FilePath $venvPy -ArgumentList @('-m','uvicorn','api.pras_api:app','--host','127.0.0.1','--port','5004') `
# -WorkingDirectory $root -WindowStyle Normal

$procs = @()

# API on 5004 (FASTAPI)
$procs += Start-Process -FilePath $venvPy `
  -ArgumentList @('-m','uvicorn','api.pras_api:app','--host','127.0.0.1','--port','5004') `
  -WorkingDirectory $root -PassThru `
  -RedirectStandardOutput "$root\logs\api.out.log" `
  -RedirectStandardError  "$root\logs\api.err.log"

# Dedicated WS on 5005 (stand-alone)
$procs += Start-Process -FilePath $venvPy `
  -ArgumentList @('-m','api.services.ws_service.ws_server') `
  -WorkingDirectory $root -PassThru `
  -RedirectStandardOutput "$root\logs\ws.out.log" `
  -RedirectStandardError  "$root\logs\ws.err.log"

"Started:`n" + ($procs | ForEach-Object {
    "$($_.Id): $($_.StartInfo.FileName) $($_.StartInfo.Arguments)"
}) -join "`n"

try {
    Wait-Process -Id ($procs.Id)
} finally {
    $procs | Where-Object { -not $_.HasExited } | Stop-Process
}