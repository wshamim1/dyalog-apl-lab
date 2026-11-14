#!/usr/bin/env bash
# Build the Dyalog image with the MariaDB ODBC driver (for SQAPL → MySQL).
#   ./build.sh            # uses podman
#   ENGINE=docker ./build.sh
set -euo pipefail
ENGINE="${ENGINE:-podman}"
IMAGE="${IMAGE:-localhost/dyalog-mysql:latest}"
cd "$(dirname "$0")"
"$ENGINE" build -t "$IMAGE" .
echo
echo "Built $IMAGE. Start Dyalog with it, e.g.:"
echo "  IMAGE=$IMAGE install/dyalog/podman.sh run     # terminal session"
echo "  IMAGE=$IMAGE install/dyalog/podman.sh ride    # for RIDE / the Python tools"
