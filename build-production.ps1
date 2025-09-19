# Production Build Script for PRAS
Write-Host "🚀 Building PRAS for Production..." -ForegroundColor Green

# 1. Clean previous builds
Write-Host "🧹 Cleaning previous builds..." -ForegroundColor Yellow
if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
if (Test-Path "api/__pycache__") { Remove-Item -Recurse -Force "api/__pycache__" }

# 2. Install frontend dependencies
Write-Host "📦 Installing frontend dependencies..." -ForegroundColor Yellow
npm ci --only=production

# 3. Build frontend
Write-Host "🔨 Building frontend..." -ForegroundColor Yellow
npm run build

# 4. Install Python dependencies
Write-Host "🐍 Installing Python dependencies..." -ForegroundColor Yellow
pip install -r api/requirements_clean.txt

# 5. Create production directories
Write-Host "📁 Creating production directories..." -ForegroundColor Yellow
$dirs = @("api/uploads", "api/pdf_output", "api/logs", "api/db")
foreach ($dir in $dirs) {
    if (!(Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force
    }
}

# 6. Copy production files
Write-Host "📋 Copying production files..." -ForegroundColor Yellow
Copy-Item "web.config" "dist/" -Force

# 7. Create production startup script
Write-Host "⚡ Creating production startup script..." -ForegroundColor Yellow
@"
@echo off
echo Starting PRAS Production Server...
cd /d "%~dp0"
uvicorn api.pras_api:app --host 0.0.0.0 --port 5004 --workers 4
"@ | Out-File -FilePath "start-production.bat" -Encoding ASCII

Write-Host "✅ Production build complete!" -ForegroundColor Green
Write-Host "📁 Built files are in the 'dist' directory" -ForegroundColor Cyan
Write-Host "🚀 Run 'start-production.bat' to start the server" -ForegroundColor Cyan
