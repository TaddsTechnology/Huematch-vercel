# AI Fashion Vercel Deployment Script
# Run this script in PowerShell to deploy your app to Vercel

param(
    [switch]$SkipBuild,
    [switch]$SkipInstall,
    [switch]$Production
)

Write-Host "🚀 AI Fashion Vercel Deployment Script" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Green

# Check if we're in the right directory
$currentDir = Get-Location
if (-not (Test-Path "vercel.json")) {
    Write-Host "❌ Error: vercel.json not found. Please run this script from the project root directory." -ForegroundColor Red
    exit 1
}

Write-Host "📍 Current directory: $currentDir" -ForegroundColor Blue

# Check if Node.js is installed
try {
    $nodeVersion = node --version
    Write-Host "✅ Node.js version: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Node.js not found. Please install Node.js first." -ForegroundColor Red
    exit 1
}

# Check if Vercel CLI is installed
try {
    $vercelVersion = vercel --version
    Write-Host "✅ Vercel CLI version: $vercelVersion" -ForegroundColor Green
} catch {
    Write-Host "⚠️ Vercel CLI not found. Installing..." -ForegroundColor Yellow
    npm install -g vercel
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to install Vercel CLI" -ForegroundColor Red
        exit 1
    }
}

# Install frontend dependencies
if (-not $SkipInstall) {
    Write-Host "📦 Installing frontend dependencies..." -ForegroundColor Blue
    Set-Location "frontend"
    npm install
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to install frontend dependencies" -ForegroundColor Red
        exit 1
    }
    Set-Location ".."
    Write-Host "✅ Frontend dependencies installed" -ForegroundColor Green
} else {
    Write-Host "⏭️ Skipping dependency installation" -ForegroundColor Yellow
}

# Build frontend
if (-not $SkipBuild) {
    Write-Host "🔨 Building frontend..." -ForegroundColor Blue
    Set-Location "frontend"
    npm run build
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Frontend build failed" -ForegroundColor Red
        exit 1
    }
    Set-Location ".."
    Write-Host "✅ Frontend built successfully" -ForegroundColor Green
} else {
    Write-Host "⏭️ Skipping frontend build" -ForegroundColor Yellow
}

# Check if user is logged in to Vercel
Write-Host "🔐 Checking Vercel authentication..." -ForegroundColor Blue
vercel whoami 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️ Not logged in to Vercel. Please log in:" -ForegroundColor Yellow
    vercel login
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Vercel login failed" -ForegroundColor Red
        exit 1
    }
}

# Deploy to Vercel
Write-Host "🚀 Deploying to Vercel..." -ForegroundColor Blue
if ($Production) {
    Write-Host "📦 Production deployment..." -ForegroundColor Magenta
    vercel --prod --yes
} else {
    Write-Host "🧪 Preview deployment..." -ForegroundColor Cyan
    vercel --yes
}

if ($LASTEXITCODE -eq 0) {
    Write-Host "🎉 Deployment successful!" -ForegroundColor Green
    Write-Host "📡 Your app is now live on Vercel" -ForegroundColor Green
    Write-Host "" -ForegroundColor White
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "1. Set environment variables in Vercel dashboard" -ForegroundColor White
    Write-Host "2. Test your API endpoints" -ForegroundColor White
    Write-Host "3. Configure custom domain (optional)" -ForegroundColor White
} else {
    Write-Host "❌ Deployment failed" -ForegroundColor Red
    Write-Host "Check the error messages above for details" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "🔗 Useful links:" -ForegroundColor Blue
Write-Host "- Vercel Dashboard: https://vercel.com/dashboard" -ForegroundColor White
Write-Host "- Documentation: See VERCEL_DEPLOYMENT.md" -ForegroundColor White
