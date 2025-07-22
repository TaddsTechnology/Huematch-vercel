#!/bin/bash

# AI Fashion App - Docker Build and Push Script
# This script builds Docker images for both frontend and backend and pushes them to a registry

set -e  # Exit on any error

# Configuration
REGISTRY="your-registry"  # Replace with your Docker registry (e.g., docker.io/username, ghcr.io/username)
PROJECT_NAME="ai-fashion"
VERSION="${1:-latest}"  # Use first argument as version, default to "latest"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 AI Fashion App - Docker Build and Push${NC}"
echo -e "${BLUE}======================================${NC}"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker and try again.${NC}"
    exit 1
fi

# Function to build and push image
build_and_push() {
    local service=$1
    local context=$2
    local dockerfile=$3
    local image_name="${REGISTRY}/${PROJECT_NAME}-${service}:${VERSION}"
    
    echo -e "${YELLOW}📦 Building ${service} image...${NC}"
    
    # Build the image
    if docker build -t "${image_name}" -f "${dockerfile}" "${context}"; then
        echo -e "${GREEN}✅ Successfully built ${image_name}${NC}"
    else
        echo -e "${RED}❌ Failed to build ${service} image${NC}"
        exit 1
    fi
    
    # Push the image
    echo -e "${YELLOW}🚀 Pushing ${service} image to registry...${NC}"
    if docker push "${image_name}"; then
        echo -e "${GREEN}✅ Successfully pushed ${image_name}${NC}"
    else
        echo -e "${RED}❌ Failed to push ${service} image${NC}"
        exit 1
    fi
    
    echo -e "${BLUE}📋 Image URL: ${image_name}${NC}"
    echo ""
}

# Build and push backend
echo -e "${BLUE}🔧 Building Backend Service${NC}"
build_and_push "backend" "./backend" "./backend/Dockerfile"

# Build and push frontend
echo -e "${BLUE}🎨 Building Frontend Service${NC}"
build_and_push "frontend" "./frontend" "./frontend/Dockerfile"

# Summary
echo -e "${GREEN}🎉 All images built and pushed successfully!${NC}"
echo -e "${BLUE}📝 Deployment URLs:${NC}"
echo -e "   Backend:  ${REGISTRY}/${PROJECT_NAME}-backend:${VERSION}"
echo -e "   Frontend: ${REGISTRY}/${PROJECT_NAME}-frontend:${VERSION}"
echo ""
echo -e "${YELLOW}📖 Next Steps:${NC}"
echo -e "   1. Go to Render dashboard: https://dashboard.render.com"
echo -e "   2. Create new Web Service"
echo -e "   3. Select 'Deploy an existing image'"
echo -e "   4. Use the image URLs above"
echo -e "   5. Configure environment variables as per deploy-render.md"
echo ""
echo -e "${GREEN}✨ Happy deploying!${NC}"
