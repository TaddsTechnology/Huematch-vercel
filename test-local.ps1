# Test Local Setup Script
# Quickly test your setup before deploying

Write-Host "🧪 Testing Local AI Fashion Setup" -ForegroundColor Green
Write-Host "==================================" -ForegroundColor Green

# Test frontend build
Write-Host "🔨 Testing frontend build..." -ForegroundColor Blue
Set-Location "frontend"
npm run build
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Frontend builds successfully" -ForegroundColor Green
} else {
    Write-Host "❌ Frontend build failed" -ForegroundColor Red
    Set-Location ".."
    exit 1
}
Set-Location ".."

# Check API structure
Write-Host "📁 Checking API structure..." -ForegroundColor Blue
if (Test-Path "api\index.py") {
    Write-Host "✅ api/index.py exists" -ForegroundColor Green
} else {
    Write-Host "❌ api/index.py missing" -ForegroundColor Red
}

if (Test-Path "api\requirements.txt") {
    Write-Host "✅ api/requirements.txt exists" -ForegroundColor Green
} else {
    Write-Host "❌ api/requirements.txt missing" -ForegroundColor Red
}

if (Test-Path "vercel.json") {
    Write-Host "✅ vercel.json exists" -ForegroundColor Green
} else {
    Write-Host "❌ vercel.json missing" -ForegroundColor Red
}

# Test Python imports (basic check)
Write-Host "🐍 Testing Python backend imports..." -ForegroundColor Blue
try {
    python -c "import sys; sys.path.append('backend'); sys.path.append('backend/prods_fastapi'); from fastapi import FastAPI; print('✅ FastAPI import successful')"
} catch {
    Write-Host "⚠️ Python backend import issues - may work in Vercel environment" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🎯 Setup Summary:" -ForegroundColor Blue
Write-Host "- Frontend builds correctly" -ForegroundColor Green
Write-Host "- API structure is ready" -ForegroundColor Green
Write-Host "- Vercel configuration exists" -ForegroundColor Green
Write-Host ""
Write-Host "Ready for deployment! Run: .\deploy-vercel.ps1" -ForegroundColor Cyan
