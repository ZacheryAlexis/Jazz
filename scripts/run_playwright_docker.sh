#!/usr/bin/env bash
set -euo pipefail

# Build and run Playwright tests inside Docker to avoid host dependency issues.
# Usage: ./scripts/run_playwright_docker.sh

IMAGE_NAME="jazz-playwright:local"
DOCKERFILE_PATH="./docker/playwright.Dockerfile"

echo "Building Playwright test image..."
docker build -f "$DOCKERFILE_PATH" -t "$IMAGE_NAME" .

echo "Running Playwright tests in container..."
docker run --rm \
  -e CI=true \
  "$IMAGE_NAME"

echo "Playwright tests finished."
