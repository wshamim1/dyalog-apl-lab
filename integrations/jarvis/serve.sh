#!/usr/bin/env bash
# Start the Jarvis JSON API in a Dyalog container.
#   integrations/jarvis/serve.sh [port]     (default 8080)
# Then:  curl -s -X POST localhost:8080/Sum -H 'Content-Type: application/json' -d '[1,2,3]'
#
# Env: DYALOG_ENGINE (podman|docker), IMAGE (default docker.io/dyalog/dyalog),
#      HOST: address to listen on (default 127.0.0.1 = this computer only;
#            0.0.0.0 makes it reachable from your network, and it has no login)
set -euo pipefail
PORT="${1:-8080}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../.." && pwd)"
IMAGE="${IMAGE:-docker.io/dyalog/dyalog}"
HOST="${HOST:-127.0.0.1}"
if [ -z "${DYALOG_ENGINE:-}" ]; then
  if command -v podman >/dev/null 2>&1; then DYALOG_ENGINE=podman; else DYALOG_ENGINE=docker; fi
fi
"$DYALOG_ENGINE" info >/dev/null 2>&1 || {
  echo "error: $DYALOG_ENGINE isn't running (try: podman machine start)" >&2; exit 1; }

tty=(-i); [ -t 0 ] && [ -t 1 ] && tty=(-it)
# The repo is mounted read-only: the API only needs to read its code.
# LOAD makes Dyalog load Server.apln at startup and call Server.Run.
exec "$DYALOG_ENGINE" run "${tty[@]}" --rm \
  -p "$HOST:$PORT:$PORT" -e "PORT=$PORT" \
  -v "$REPO:/app:ro" -w /app \
  -e LOAD=/app/integrations/jarvis/Server.apln \
  "$IMAGE"
