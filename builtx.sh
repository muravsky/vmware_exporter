#!/bin/bash

set -e

# Configuration
DOCKER_USERNAME="muravsky"
IMAGE_NAME="vmware-exporter"
VERSION="1.0"

echo "Setting up Docker buildx for multi-platform builds..."

# Remove existing builder if it exists
docker buildx rm ${IMAGE_NAME}-builder 2>/dev/null || true

# Create new builder with proper configuration
docker buildx create \
  --name ${IMAGE_NAME}-builder \
  --driver docker-container \
  --driver-opt network=host \
  --use

# Bootstrap the builder
docker buildx inspect --bootstrap

echo "Building for linux/amd64..."
docker buildx build \
  --platform linux/amd64 \
  --tag ${DOCKER_USERNAME}/${IMAGE_NAME}:latest \
  --tag ${DOCKER_USERNAME}/${IMAGE_NAME}:v${VERSION} \
  --push \
  .

echo "Attempting to build for linux/arm64..."
if docker buildx build \
  --platform linux/arm64 \
  --tag ${DOCKER_USERNAME}/${IMAGE_NAME}:latest-arm64 \
  --tag ${DOCKER_USERNAME}/${IMAGE_NAME}:v${VERSION}-arm64 \
  --push \
  .; then
  echo "ARM64 build successful"
  
  # Create multi-arch manifest
  echo "Creating multi-arch manifest..."
  docker buildx imagetools create \
    --tag ${DOCKER_USERNAME}/${IMAGE_NAME}:latest \
    ${DOCKER_USERNAME}/${IMAGE_NAME}:latest \
    ${DOCKER_USERNAME}/${IMAGE_NAME}:latest-arm64
else
  echo "ARM64 build failed, continuing with AMD64 only"
fi

echo "Build completed successfully"
