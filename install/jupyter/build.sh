#!/usr/bin/env bash
# Build the Dyalog + JupyterLab image.   ENGINE=docker ./build.sh  to use Docker
set -euo pipefail
ENGINE="${ENGINE:-podman}"
IMAGE="${IMAGE:-localhost/dyalog-jupyter:latest}"
cd "$(dirname "$0")"
"$ENGINE" build -t "$IMAGE" .
echo "Built $IMAGE"
