# Quick Docker Setup Test
# This script tests if Docker is ready for building your images

Write-Host "🧪 Testing Docker Setup for AI Fashion App" -ForegroundColor Blue
Write-Host "==========================================" -ForegroundColor Blue
Write-Host ""

# Test 1: Check if Docker is running
Write-Host "1️⃣  Testing Docker installation..." -ForegroundColor Yellow
try {
    $dockerVersion = docker --version
    Write-Host "✅ Docker is installed: $dockerVersion" -ForegroundColor Green
    
    docker info | Out-Null
    Write-Host "✅ Docker daemon is running" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker is not running or not installed" -ForegroundColor Red
    Write-Host "   Please install Docker Desktop and start it" -ForegroundColor Yellow
    exit 1
}

# Test 2: Check if required files exist
Write-Host ""
Write-Host "2️⃣  Checking required files..." -ForegroundColor Yellow

$requiredFiles = @(
    "./backend/Dockerfile",
    "./frontend/Dockerfile", 
    "./backend/requirements.txt",
    "./frontend/package.json"
)

foreach ($file in $requiredFiles) {
    if (Test-Path $file) {
        Write-Host "✅ Found: $file" -ForegroundColor Green
    } else {
        Write-Host "❌ Missing: $file" -ForegroundColor Red
        $hasError = $true
    }
}

if ($hasError) {
    Write-Host "❌ Some required files are missing. Please check your project structure." -ForegroundColor Red
    exit 1
}

# Test 3: Check Docker Hub connection
Write-Host ""
Write-Host "3️⃣  Testing Docker Hub connectivity..." -ForegroundColor Yellow
try {
    $dockerHubTest = docker search hello-world --limit 1 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Docker Hub is accessible" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Docker Hub connection test failed - but this might be OK" -ForegroundColor Yellow
        Write-Host "   You can still push images after logging in" -ForegroundColor Gray
    }
} catch {
    Write-Host "⚠️  Could not test Docker Hub connectivity" -ForegroundColor Yellow
}

# Test 4: Check available disk space
Write-Host ""
Write-Host "4️⃣  Checking disk space..." -ForegroundColor Yellow
$diskSpace = Get-WmiObject -Class Win32_LogicalDisk -Filter "DeviceID='C:'" | Select-Object @{Name="FreeSpaceGB";Expression={[math]::Round($_.FreeSpace/1GB,2)}}
$freeSpaceGB = $diskSpace.FreeSpaceGB

if ($freeSpaceGB -gt 5) {
    Write-Host "✅ Available disk space: $freeSpaceGB GB" -ForegroundColor Green
} else {
    Write-Host "⚠️  Low disk space: $freeSpaceGB GB (Docker builds need ~3-5 GB)" -ForegroundColor Yellow
}

# Summary
Write-Host ""
Write-Host "📋 Setup Summary:" -ForegroundColor Blue
Write-Host "=================" -ForegroundColor Blue
Write-Host "✅ Docker is ready for building images" -ForegroundColor Green
Write-Host "✅ All required files are present" -ForegroundColor Green
Write-Host "✅ System is ready for deployment" -ForegroundColor Green
Write-Host ""
Write-Host "🚀 Next Steps:" -ForegroundColor Yellow
Write-Host "1. Run: .\build-docker-images.ps1" -ForegroundColor Cyan
Write-Host "2. Follow the DOCKER-DEPLOYMENT-GUIDE.md" -ForegroundColor Cyan
Write-Host ""
Write-Host "💡 Tips:" -ForegroundColor Blue
Write-Host "- Have your Docker Hub username ready" -ForegroundColor Gray
Write-Host "- The build process may take 10-15 minutes" -ForegroundColor Gray
Write-Host "- Make sure you have stable internet connection" -ForegroundColor Gray
