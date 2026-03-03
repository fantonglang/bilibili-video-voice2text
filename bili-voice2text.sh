#!/bin/bash
#
# Bilibili Video Voice to Text - Docker Wrapper Script
#
# This script runs the bili-voice2text tool in a Docker container.
# The container is automatically removed after completion (--rm).
#
# Usage:
#   ./bili-voice2text.sh                    # Interactive mode
#   ./bili-voice2text.sh -bv BV1xx411c7mD   # Process single video
#   ./bili-voice2text.sh -bv BV1 BV2 BV3    # Process multiple videos
#

# Configuration
IMAGE_NAME="bili-voice2text"
IMAGE_TAG="latest"
CONTAINER_NAME="bili-voice2text-$(date +%s)"

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored messages
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

# Check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi

    if ! docker info &> /dev/null; then
        print_error "Docker daemon is not running. Please start Docker first."
        exit 1
    fi
}

# Build Docker image with retry logic
build_image() {
    if docker image inspect "${IMAGE_NAME}:${IMAGE_TAG}" &> /dev/null; then
        print_info "Using existing Docker image: ${IMAGE_NAME}:${IMAGE_TAG}"
        return 0
    fi

    print_step "Docker image not found. Building..."
    cd "${SCRIPT_DIR}"

    # Try different build methods
    local build_methods=(
        "docker build -t ${IMAGE_NAME}:${IMAGE_TAG} ."
        "docker build --network=host -t ${IMAGE_NAME}:${IMAGE_TAG} ."
    )

    # If mirror Dockerfile exists, try it too
    if [ -f "Dockerfile.mirror" ]; then
        build_methods+=("docker build -f Dockerfile.mirror -t ${IMAGE_NAME}:${IMAGE_TAG} .")
    fi

    for method in "${build_methods[@]}"; do
        print_info "Trying: $method"
        if eval "$method"; then
            print_info "Docker image built successfully!"
            return 0
        fi
        print_warn "Build method failed, trying alternative..."
    done

    print_error "All build attempts failed!"
    echo ""
    echo "Troubleshooting options:"
    echo "  1. Check your internet connection"
    echo "  2. Run the build script manually: ./build-docker.sh"
    echo "  3. Use a Docker mirror if you're in China:"
    echo "     docker pull docker.mirrors.sjtug.sjtu.edu.cn/library/python:3.11-slim"
    echo "     docker tag docker.mirrors.sjtug.sjtu.edu.cn/library/python:3.11-slim python:3.11-slim"
    echo "  4. Check Docker logs: docker system info"

    return 1
}

# Run the container
run_container() {
    local args="$@"

    print_step "Starting container: ${CONTAINER_NAME}"
    if [ -z "$args" ]; then
        print_info "Mode: Interactive"
    else
        print_info "Arguments: $args"
    fi
    print_info "Volumes:"
    print_info "  - ${SCRIPT_DIR}/outputs -> /app/outputs"
    print_info "  - ${SCRIPT_DIR}/bilibili_video -> /app/bilibili_video"
    print_info "  - ${SCRIPT_DIR}/.env -> /app/.env"
    
    # Check for cookies file
    local cookie_mount=""
    if [ -f "${SCRIPT_DIR}/cookies.txt" ]; then
        print_info "  - ${SCRIPT_DIR}/cookies.txt -> /app/cookies.txt"
        cookie_mount="-v ${SCRIPT_DIR}/cookies.txt:/app/cookies.txt:ro"
    fi

    # Run container with --rm to auto-remove after completion
    # Mount volumes for persistent data
    docker run -it --rm \
        --name "${CONTAINER_NAME}" \
        -v "${SCRIPT_DIR}/outputs:/app/outputs" \
        -v "${SCRIPT_DIR}/bilibili_video:/app/bilibili_video" \
        -v "${SCRIPT_DIR}/.env:/app/.env:ro" \
        ${cookie_mount} \
        "${IMAGE_NAME}:${IMAGE_TAG}" \
        ${args}

    local exit_code=$?

    if [ $exit_code -eq 0 ]; then
        print_info "Container completed successfully and was removed."
    else
        print_error "Container exited with code ${exit_code}."
    fi

    return $exit_code
}

# Show help
show_help() {
    echo "Bilibili Video Voice to Text - Docker Wrapper"
    echo ""
    echo "Usage:"
    echo "  $0                    # Interactive mode"
    echo "  $0 -bv BV1xx411c7mD   # Process single video"
    echo "  $0 -bv BV1 BV2 BV3    # Process multiple videos"
    echo "  $0 --help             # Show this help"
    echo "  $0 --rebuild          # Force rebuild Docker image"
    echo ""
    echo "Examples:"
    echo "  $0 -bv BV1xx411c7mD"
    echo "  $0 -bv BV1xx411c7mD BV1yy822d9nE BV1zz333e4fA"
}

# Main function
main() {
    # Handle special flags
    if [[ "$1" == "--help" ]] || [[ "$1" == "-h" ]]; then
        show_help
        exit 0
    fi

    if [[ "$1" == "--rebuild" ]]; then
        print_warn "Force rebuilding Docker image..."
        docker rmi "${IMAGE_NAME}:${IMAGE_TAG}" 2>/dev/null || true
        shift
    fi

    echo "===================================="
    echo "Bilibili Video Voice to Text"
    echo "===================================="
    echo ""

    # Check prerequisites
    check_docker

    # Build image if needed
    if ! build_image; then
        exit 1
    fi

    # Run container with all provided arguments
    run_container "$@"

    exit $?
}

# Execute main function
main "$@"
