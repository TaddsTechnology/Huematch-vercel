#!/bin/bash

# AI Fashion Docker Startup Script
# This script helps you easily start the AI Fashion application with Docker

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 AI Fashion Docker Startup Script${NC}"
echo -e "${BLUE}======================================${NC}"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed. Please install Docker first.${NC}"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose is not installed. Please install Docker Compose first.${NC}"
    exit 1
fi

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo -e "${RED}❌ Docker is not running. Please start Docker first.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker and Docker Compose are available${NC}"

# Function to show help
show_help() {
    echo -e "${YELLOW}Usage: $0 [OPTION]${NC}"
    echo ""
    echo "Options:"
    echo "  dev       Start in development mode (default)"
    echo "  prod      Start in production mode"
    echo "  build     Build images without starting"
    echo "  stop      Stop all containers"
    echo "  clean     Stop containers and remove images"
    echo "  logs      Show logs"
    echo "  status    Show container status"
    echo "  help      Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0              # Start in development mode"
    echo "  $0 dev          # Start in development mode"
    echo "  $0 prod         # Start in production mode"
    echo "  $0 build        # Build images"
    echo "  $0 stop         # Stop all containers"
    echo "  $0 clean        # Clean up everything"
}

# Function to check if services are running
check_services() {
    echo -e "${BLUE}🔍 Checking service status...${NC}"
    
    # Check if backend is responding
    if curl -s -f http://localhost:8000/ > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Backend is running at http://localhost:8000${NC}"
    else
        echo -e "${YELLOW}⚠️  Backend is not responding yet${NC}"
    fi
    
    # Check if frontend is responding
    if curl -s -f http://localhost:3000/ > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Frontend is running at http://localhost:3000${NC}"
    else
        echo -e "${YELLOW}⚠️  Frontend is not responding yet${NC}"
    fi
}

# Function to show service URLs
show_urls() {
    echo -e "${GREEN}🌐 Service URLs:${NC}"
    echo -e "${BLUE}   Frontend:        http://localhost:3000${NC}"
    echo -e "${BLUE}   Backend API:     http://localhost:8000${NC}"
    echo -e "${BLUE}   API Docs:        http://localhost:8000/docs${NC}"
    echo -e "${BLUE}   API Redoc:       http://localhost:8000/redoc${NC}"
}

# Parse command line arguments
case "${1:-dev}" in
    "dev"|"development")
        echo -e "${BLUE}🔧 Starting in development mode...${NC}"
        docker-compose up --build -d
        echo -e "${GREEN}✅ Services started successfully!${NC}"
        show_urls
        echo ""
        echo -e "${YELLOW}💡 Use 'docker-compose logs -f' to view logs${NC}"
        echo -e "${YELLOW}💡 Use '$0 stop' to stop services${NC}"
        ;;
    
    "prod"|"production")
        echo -e "${BLUE}🏭 Starting in production mode...${NC}"
        docker-compose -f docker-compose.yml -f docker-compose.prod.yml up --build -d
        echo -e "${GREEN}✅ Services started successfully!${NC}"
        show_urls
        echo ""
        echo -e "${YELLOW}💡 Use 'docker-compose logs -f' to view logs${NC}"
        echo -e "${YELLOW}💡 Use '$0 stop' to stop services${NC}"
        ;;
    
    "build")
        echo -e "${BLUE}🏗️  Building Docker images...${NC}"
        docker-compose build
        echo -e "${GREEN}✅ Images built successfully!${NC}"
        ;;
    
    "stop")
        echo -e "${YELLOW}🛑 Stopping all containers...${NC}"
        docker-compose down
        echo -e "${GREEN}✅ All containers stopped${NC}"
        ;;
    
    "clean")
        echo -e "${YELLOW}🧹 Stopping containers and removing images...${NC}"
        docker-compose down
        docker-compose down --rmi all --volumes --remove-orphans
        echo -e "${GREEN}✅ Cleanup completed${NC}"
        ;;
    
    "logs")
        echo -e "${BLUE}📋 Showing logs...${NC}"
        docker-compose logs -f
        ;;
    
    "status")
        echo -e "${BLUE}📊 Container status:${NC}"
        docker-compose ps
        echo ""
        check_services
        ;;
    
    "help"|"-h"|"--help")
        show_help
        ;;
    
    *)
        echo -e "${RED}❌ Unknown option: $1${NC}"
        show_help
        exit 1
        ;;
esac
