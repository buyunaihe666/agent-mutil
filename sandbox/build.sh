#!/bin/bash
set -e

echo "Building NEXUS sandbox Docker image..."
docker build -t nexus-sandbox:latest .
echo "Sandbox image built successfully: nexus-sandbox:latest"
