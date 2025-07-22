# Simple Docker Build and Push Script
param(
    [string]$DockerUsername = "newbie028",
    [string]$Version = "latest"
)

$ProjectName = "ai-fashion"

Write-Host "Building Docker Images for AI Fashion App" -ForegroundColor Blue
Write-Host "Username: $DockerUsername" -ForegroundColor Green
Write-Host ""

# Build Backend
Write-Host "Building Backend Image..." -ForegroundColor Yellow
$BackendImage = "${DockerUsername}/${ProjectName}-backend:${Version}"
docker build -t $BackendImage -f ./backend/Dockerfile ./backend

if ($LASTEXITCODE -eq 0) {
    Write-Host "Backend build successful!" -ForegroundColor Green
    
    Write-Host "Pushing backend to Docker Hub..." -ForegroundColor Yellow
    docker push $BackendImage
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Backend pushed successfully!" -ForegroundColor Green
    } else {
        Write-Host "Backend push failed!" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "Backend build failed!" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Build Frontend
Write-Host "Building Frontend Image..." -ForegroundColor Yellow
$FrontendImage = "${DockerUsername}/${ProjectName}-frontend:${Version}"
docker build -t $FrontendImage -f ./frontend/Dockerfile ./frontend

if ($LASTEXITCODE -eq 0) {
    Write-Host "Frontend build successful!" -ForegroundColor Green
    
    Write-Host "Pushing frontend to Docker Hub..." -ForegroundColor Yellow
    docker push $FrontendImage
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Frontend pushed successfully!" -ForegroundColor Green
    } else {
        Write-Host "Frontend push failed!" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "Frontend build failed!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "SUCCESS! Your images are ready:" -ForegroundColor Green
Write-Host "Backend:  $BackendImage" -ForegroundColor Cyan
Write-Host "Frontend: $FrontendImage" -ForegroundColor Cyan
Write-Host ""
Write-Host "Now deploy these on Render:" -ForegroundColor Yellow
Write-Host "1. Go to https://dashboard.render.com"
Write-Host "2. Click New + -> Web Service"
Write-Host "3. Select 'Deploy an existing image'"
Write-Host "4. Use the image URLs above"
