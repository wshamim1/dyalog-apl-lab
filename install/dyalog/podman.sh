#!/usr/bin/env bash
# Run Dyalog APL with Podman. See container.sh / podman.md.
#   ./podman.sh install | pull | run | ride
ENGINE=podman SELF="$0" exec "$(dirname "$0")/container.sh" "$@"
