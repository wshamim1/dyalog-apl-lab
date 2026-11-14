#!/usr/bin/env bash
# Run Dyalog APL with Docker. See container.sh / docker.md.
#   ./docker.sh install | pull | run | ride
ENGINE=docker SELF="$0" exec "$(dirname "$0")/container.sh" "$@"
