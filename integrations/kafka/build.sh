#!/usr/bin/env bash
# Build the Dyalog + Kafka image.   ENGINE=docker ./build.sh  to use Docker
set -euo pipefail
ENGINE="${ENGINE:-podman}"
IMAGE="${IMAGE:-localhost/dyalog-kafka:latest}"
cd "$(dirname "$0")"
"$ENGINE" build -t "$IMAGE" .
echo "Built $IMAGE"
