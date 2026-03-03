#!/bin/bash
#
# Docker build script with network timeout handling and mirror support
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

IMAGE_NAME="bili-voice2text"
IMAGE_TAG="latest"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Test Docker Hub connectivity
test_docker_hub() {
    print_step "Testing Docker Hub connectivity..."
    if timeout 10 docker pull hello-world &>/dev/null; then
        print_info "Docker Hub is accessible"
        return 0
    else
        print_warn "Docker Hub connection failed or timed out"
        return 1
    fi
}

# Build with standard Dockerfile
build_standard() {
    print_step "Building with standard Dockerfile..."
    docker build -t "${IMAGE_NAME}:${IMAGE_TAG}" . 2>&1
}

# Build with mirror Dockerfile
build_mirror() {
    print_step "Building with mirror registry (SJTU mirror)..."
    if [ -f "Dockerfile.mirror" ]; then
        docker build -f Dockerfile.mirror -t "${IMAGE_NAME}:${IMAGE_TAG}" . 2>&1
    else
        print_error "Dockerfile.mirror not found!"
        return 1
    fi
}

# Build with explicit platform (sometimes helps with network issues)
build_with_platform() {
    print_step "Building with platform specification..."
    docker build --platform linux/amd64 -t "${IMAGE_NAME}:${IMAGE_TAG}" . 2>&1
}

# Main build process
main() {
    echo "===================================="
    echo "Docker Build Script"
    echo "===================================="
    echo ""

    # Check if Docker is running
    if ! docker info &>/dev/null; then
        print_error "Docker daemon is not running!"
        exit 1
    fi

    # Check if image already exists
    if docker image inspect "${IMAGE_NAME}:${IMAGE_TAG}" &>/dev/null; then
        print_warn "Image ${IMAGE_NAME}:${IMAGE_TAG} already exists!"
        read -p "Rebuild? (y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_info "Using existing image"
            exit 0
        fi
        docker rmi "${IMAGE_NAME}:${IMAGE_TAG}" 2>/dev/null || true
    fi

    # Try standard build first
    print_info "Attempting standard build..."
    if build_standard; then
        print_info "Build successful!"
        exit 0
    fi

    print_warn "Standard build failed, trying alternatives..."

    # Try with mirror
    if build_mirror; then
        print_info "Build with mirror successful!"
        exit 0
    fi

    # Try with platform
    if build_with_platform; then
        print_info "Build with platform successful!"
        exit 0
    fi

    print_error "All build attempts failed!"
    echo ""
    echo "Possible solutions:"
    echo "  1. Check your internet connection"
    echo "  2. Configure Docker to use a mirror registry:"
    echo "     Edit /etc/docker/daemon.json and add:"
    echo '     {"registry-mirrors": ["https://docker.mirrors.ustc.edu.cn"]}'
    echo "  3. Use a VPN if you're in a restricted region"
    echo "  4. Pull the base image manually:"
    echo "     docker pull python:3.11-slim"
    echo "  5. Try building with --network=host:"
    echo "     docker build --network=host -t bili-voice2text ."

    exit 1
}

main "$@"
