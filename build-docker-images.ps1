# AI Fashion App - Enhanced Docker Build and Push Script
# This script builds Docker images and pushes them to Docker Hub or another registry

param(
    [string]$Version = "latest",
    [string]$DockerUsername = "",
    [string]$Registry = "docker.io"
)

$ProjectName = "ai-fashion"

Write-Host "🚀 AI Fashion - Docker Image Builder" -ForegroundColor Blue
Write-Host "=================================" -ForegroundColor Blue
Write-Host ""

# Prompt for Docker username if not provided
if ([string]::IsNullOrEmpty($DockerUsername)) {
    $DockerUsername = Read-Host "Enter your Docker Hub username"
    if ([string]::IsNullOrEmpty($DockerUsername)) {
        Write-Host "❌ Docker username is required!" -ForegroundColor Red
        exit 1
    }
}

# Check if Docker is running
try {
    docker info | Out-Null
    Write-Host "✅ Docker is running" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker is not running. Please start Docker Desktop and try again." -ForegroundColor Red
    exit 1
}

# Login to Docker Hub
Write-Host "🔐 Please login to Docker Hub..." -ForegroundColor Yellow
$loginResult = docker login
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Docker login failed. Please check your credentials." -ForegroundColor Red
    exit 1
}
Write-Host "✅ Successfully logged in to Docker Hub" -ForegroundColor Green
Write-Host ""

# Function to build and push image
function Build-And-Push {
    param(
        [string]$Service,
        [string]$Context,
        [string]$Dockerfile
    )
    
    $ImageName = "${DockerUsername}/${ProjectName}-${Service}:${Version}"
    
    Write-Host "📦 Building $Service image..." -ForegroundColor Yellow
    Write-Host "   Context: $Context" -ForegroundColor Gray
    Write-Host "   Dockerfile: $Dockerfile" -ForegroundColor Gray
    Write-Host "   Image: $ImageName" -ForegroundColor Gray
    Write-Host ""
    
    # Build the image
    Write-Host "🔨 Building image..." -ForegroundColor Cyan
    docker build -t $ImageName -f $Dockerfile $Context
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Successfully built $ImageName" -ForegroundColor Green
    } else {
        Write-Host "❌ Failed to build $Service image" -ForegroundColor Red
        exit 1
    }
    
    # Push the image
    Write-Host "🚀 Pushing $Service image to Docker Hub..." -ForegroundColor Yellow
    docker push $ImageName
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Successfully pushed $ImageName" -ForegroundColor Green
    } else {
        Write-Host "❌ Failed to push $Service image" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "📋 Image URL: $ImageName" -ForegroundColor Blue
    Write-Host ""
    
    return $ImageName
}

# Build backend image
Write-Host "🔧 Building Backend Service" -ForegroundColor Blue
Write-Host "----------------------------" -ForegroundColor Blue
$BackendImage = Build-And-Push -Service "backend" -Context "./backend" -Dockerfile "./backend/Dockerfile"

# Build frontend image  
Write-Host "🎨 Building Frontend Service" -ForegroundColor Blue
Write-Host "----------------------------" -ForegroundColor Blue
$FrontendImage = Build-And-Push -Service "frontend" -Context "./frontend" -Dockerfile "./frontend/Dockerfile"

# Summary
Write-Host "🎉 All images built and pushed successfully!" -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Green
Write-Host ""
Write-Host "📝 Your Docker Images:" -ForegroundColor Blue
Write-Host "   Backend:  $BackendImage" -ForegroundColor Cyan
Write-Host "   Frontend: $FrontendImage" -ForegroundColor Cyan
Write-Host ""
Write-Host "📖 Next Steps for Render Deployment:" -ForegroundColor Yellow
Write-Host "   1. Go to https://dashboard.render.com" 
Write-Host "   2. Click 'New +' → 'Web Service'"
Write-Host "   3. Select 'Deploy an existing image'"
Write-Host "   4. For Backend: Use image '$BackendImage'"
Write-Host "   5. For Frontend: Use image '$FrontendImage'"
Write-Host ""
Write-Host "⚙️  Environment Variables Needed:" -ForegroundColor Yellow
Write-Host "   Backend:"
Write-Host "     - PYTHONPATH=/app"
Write-Host "     - PYTHONUNBUFFERED=1"
Write-Host "     - ENV=production"
Write-Host ""
Write-Host "   Frontend:"
Write-Host "     - NODE_ENV=production"
Write-Host "     - VITE_API_URL=https://your-backend-url.render.com"
Write-Host ""
Write-Host "✨ Ready to deploy on Render!" -ForegroundColor Green

# Save deployment info to file
$DeployInfo = @{
    backend_image = $BackendImage
    frontend_image = $FrontendImage
    version = $Version
    timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
}

$DeployInfo | ConvertTo-Json | Out-File -FilePath "deployment-images.json" -Encoding UTF8
Write-Host "📄 Deployment info saved to deployment-images.json" -ForegroundColor Gray
