# start_pras.ps1

$ErrorActionPreference = "Stop"

# Geting environment variable to create the venv
$Base = $env:PRAS_HOME
if (-not $Base -or -not (Test-Path)) {
    $Base = $PSScriptRoot
    $RequirementsPath = Join-Path $Base "/api/requirements.txt"
}

$VenvPy = Join-Path $Base ".PRAS_VENV\Scripts\python.exe"
if (-not (Test-Path $VenvPy)) {
    Write-Host "No .PRAS_VENV found, creating one..."
    py -3.12 -m venv (Join-Path $Base ".PRAS_VENV")
    & $VenvPy -m pip install --upgrade pip
    & $VenvPy -m pip install -r (Join-Path $Base "requirements.txt")
}

# Choose local venv but default
$Python = if (Test-Path $VenvPy) {
    $VenvPy
} else {
    Write-Host "No {$VenvPy} found, exiting..."
    exit 1
}

# Logs
$LogDir = Join-Path $Base "logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$Log = Join-Path $LogDir ("uvicorn_{0:yyyyMMdd_HHmmss}.log" -f (Get-Date))

# Alway bind to loopbackk
$App = "api.pras_api:app"

$Args = @("-m","uvicorn","--app-dir",$Base,$App,"--host","127.0.0.1","--port","5004","--log-level","info")

if ($Python -eq "py") {
    & py @Args *> $Log 2>&1
} else {
    & $Python @Args *> $Log 2>&1
}