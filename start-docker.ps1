# AI Fashion Docker Startup Script for Windows PowerShell
# This script helps you easily start the AI Fashion application with Docker

param(
    [string]$Command = "dev"
)

# Colors for output
$RED = "Red"
$GREEN = "Green"
$YELLOW = "Yellow"
$BLUE = "Blue"
$WHITE = "White"

Write-Host "🚀 AI Fashion Docker Startup Script" -ForegroundColor $BLUE
Write-Host "======================================" -ForegroundColor $BLUE

# Function to check if a command exists
function Test-Command {
    param([string]$Command)
    try {
        if (Get-Command $Command -ErrorAction Stop) {
            return $true
        }
    }
    catch {
        return $false
    }
}

# Check if Docker is installed
if (-not (Test-Command "docker")) {
    Write-Host "❌ Docker is not installed. Please install Docker first." -ForegroundColor $RED
    exit 1
}

# Check if Docker Compose is installed
if (-not (Test-Command "docker-compose")) {
    Write-Host "❌ Docker Compose is not installed. Please install Docker Compose first." -ForegroundColor $RED
    exit 1
}

# Check if Docker is running
try {
    docker info | Out-Null
    Write-Host "✅ Docker and Docker Compose are available" -ForegroundColor $GREEN
}
catch {
    Write-Host "❌ Docker is not running. Please start Docker first." -ForegroundColor $RED
    exit 1
}

# Function to show help
function Show-Help {
    Write-Host "Usage: .\start-docker.ps1 [OPTION]" -ForegroundColor $YELLOW
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  dev       Start in development mode (default)"
    Write-Host "  prod      Start in production mode"
    Write-Host "  build     Build images without starting"
    Write-Host "  stop      Stop all containers"
    Write-Host "  clean     Stop containers and remove images"
    Write-Host "  logs      Show logs"
    Write-Host "  status    Show container status"
    Write-Host "  help      Show this help message"
    Write-Host ""
    Write-Host "Examples:"
    Write-Host "  .\start-docker.ps1              # Start in development mode"
    Write-Host "  .\start-docker.ps1 dev          # Start in development mode"
    Write-Host "  .\start-docker.ps1 prod         # Start in production mode"
    Write-Host "  .\start-docker.ps1 build        # Build images"
    Write-Host "  .\start-docker.ps1 stop         # Stop all containers"
    Write-Host "  .\start-docker.ps1 clean        # Clean up everything"
}

# Function to check if services are running
function Test-Services {
    Write-Host "🔍 Checking service status..." -ForegroundColor $BLUE
    
    # Check if backend is responding
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/" -TimeoutSec 5 -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            Write-Host "✅ Backend is running at http://localhost:8000" -ForegroundColor $GREEN
        }
    }
    catch {
        Write-Host "⚠️  Backend is not responding yet" -ForegroundColor $YELLOW
    }
    
    # Check if frontend is responding
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:3000/" -TimeoutSec 5 -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            Write-Host "✅ Frontend is running at http://localhost:3000" -ForegroundColor $GREEN
        }
    }
    catch {
        Write-Host "⚠️  Frontend is not responding yet" -ForegroundColor $YELLOW
    }
}

# Function to show service URLs
function Show-URLs {
    Write-Host "🌐 Service URLs:" -ForegroundColor $GREEN
    Write-Host "   Frontend:        http://localhost:3000" -ForegroundColor $BLUE
    Write-Host "   Backend API:     http://localhost:8000" -ForegroundColor $BLUE
    Write-Host "   API Docs:        http://localhost:8000/docs" -ForegroundColor $BLUE
    Write-Host "   API Redoc:       http://localhost:8000/redoc" -ForegroundColor $BLUE
}

# Parse command line arguments
switch ($Command.ToLower()) {
    { $_ -in "dev", "development" } {
        Write-Host "🔧 Starting in development mode..." -ForegroundColor $BLUE
        docker-compose up --build -d
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Services started successfully!" -ForegroundColor $GREEN
            Show-URLs
            Write-Host ""
            Write-Host "💡 Use 'docker-compose logs -f' to view logs" -ForegroundColor $YELLOW
            Write-Host "💡 Use '.\start-docker.ps1 stop' to stop services" -ForegroundColor $YELLOW
        }
    }
    
    { $_ -in "prod", "production" } {
        Write-Host "🏭 Starting in production mode..." -ForegroundColor $BLUE
        docker-compose -f docker-compose.yml -f docker-compose.prod.yml up --build -d
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Services started successfully!" -ForegroundColor $GREEN
            Show-URLs
            Write-Host ""
            Write-Host "💡 Use 'docker-compose logs -f' to view logs" -ForegroundColor $YELLOW
            Write-Host "💡 Use '.\start-docker.ps1 stop' to stop services" -ForegroundColor $YELLOW
        }
    }
    
    "build" {
        Write-Host "🏗️  Building Docker images..." -ForegroundColor $BLUE
        docker-compose build
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Images built successfully!" -ForegroundColor $GREEN
        }
    }
    
    "stop" {
        Write-Host "🛑 Stopping all containers..." -ForegroundColor $YELLOW
        docker-compose down
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ All containers stopped" -ForegroundColor $GREEN
        }
    }
    
    "clean" {
        Write-Host "🧹 Stopping containers and removing images..." -ForegroundColor $YELLOW
        docker-compose down
        docker-compose down --rmi all --volumes --remove-orphans
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Cleanup completed" -ForegroundColor $GREEN
        }
    }
    
    "logs" {
        Write-Host "📋 Showing logs..." -ForegroundColor $BLUE
        docker-compose logs -f
    }
    
    "status" {
        Write-Host "📊 Container status:" -ForegroundColor $BLUE
        docker-compose ps
        Write-Host ""
        Test-Services
    }
    
    { $_ -in "help", "-h", "--help" } {
        Show-Help
    }
    
    default {
        Write-Host "❌ Unknown option: $Command" -ForegroundColor $RED
        Show-Help
        exit 1
    }
}
