# AI Fashion App - Docker Build and Push Script (PowerShell)
# This script builds Docker images for both frontend and backend and pushes them to a registry

param(
    [string]$Version = "latest",
    [string]$Registry = "",  # Will prompt if not provided
    [string]$Username = ""   # Docker registry username
)

$ProjectName = "ai-fashion"

# Colors for output
$Colors = @{
    Red = "Red"
    Green = "Green"
    Yellow = "Yellow"
    Blue = "Blue"
    Cyan = "Cyan"
}

Write-Host "🚀 AI Fashion App - Docker Build and Push" -ForegroundColor Blue
Write-Host "======================================" -ForegroundColor Blue
Write-Host ""

# Check if Docker is running
try {
    docker info | Out-Null
    Write-Host "✅ Docker is running" -ForegroundColor Green
}
catch {
    Write-Host "❌ Docker is not running. Please start Docker and try again." -ForegroundColor Red
    exit 1
}

# Function to build and push image
function Build-And-Push {
    param(
        [string]$Service,
        [string]$Context,
        [string]$Dockerfile
    )
    
    $ImageName = "${Registry}/${ProjectName}-${Service}:${Version}"
    
    Write-Host "📦 Building $Service image..." -ForegroundColor Yellow
    
    # Build the image
    $buildResult = docker build -t $ImageName -f $Dockerfile $Context
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Successfully built $ImageName" -ForegroundColor Green
    } else {
        Write-Host "❌ Failed to build $Service image" -ForegroundColor Red
        exit 1
    }
    
    # Push the image
    Write-Host "🚀 Pushing $Service image to registry..." -ForegroundColor Yellow
    $pushResult = docker push $ImageName
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Successfully pushed $ImageName" -ForegroundColor Green
    } else {
        Write-Host "❌ Failed to push $Service image" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "📋 Image URL: $ImageName" -ForegroundColor Blue
    Write-Host ""
}

# Build and push backend
Write-Host "🔧 Building Backend Service" -ForegroundColor Blue
Build-And-Push -Service "backend" -Context "./backend" -Dockerfile "./backend/Dockerfile"

# Build and push frontend
Write-Host "🎨 Building Frontend Service" -ForegroundColor Blue
Build-And-Push -Service "frontend" -Context "./frontend" -Dockerfile "./frontend/Dockerfile"

# Summary
Write-Host "🎉 All images built and pushed successfully!" -ForegroundColor Green
Write-Host "📝 Deployment URLs:" -ForegroundColor Blue
Write-Host "   Backend:  ${Registry}/${ProjectName}-backend:${Version}"
Write-Host "   Frontend: ${Registry}/${ProjectName}-frontend:${Version}"
Write-Host ""
Write-Host "📖 Next Steps:" -ForegroundColor Yellow
Write-Host "   1. Go to Render dashboard: https://dashboard.render.com"
Write-Host "   2. Create new Web Service"
Write-Host "   3. Select 'Deploy an existing image'"
Write-Host "   4. Use the image URLs above"
Write-Host "   5. Configure environment variables as per deploy-render.md"
Write-Host ""
Write-Host "✨ Happy deploying!" -ForegroundColor Green
