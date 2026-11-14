#!/usr/bin/env bash
# Shared logic for docker.sh and podman.sh: run Dyalog APL in a container.
# Call it through those wrappers, or directly with ENGINE=docker|podman.
#
# Usage:
#   ./docker.sh install   # install/start the engine (Homebrew) and pull the image
#   ./docker.sh pull      # pull/update the Dyalog image
#   ./docker.sh run       # interactive APL session in this terminal
#   ./docker.sh ride      # interpreter serving RIDE on port 4502
#
# The repo root (or MOUNT_DIR) is mounted at /app inside the container.
#
# Env:
#   IMAGE       image to use   (default: docker.io/dyalog/dyalog)
#   RIDE_PORT   port for ride  (default: 4502)
#   MOUNT_DIR   host folder mounted at /app (default: the repo root)

set -euo pipefail

ENGINE="${ENGINE:-docker}"
IMAGE="${IMAGE:-docker.io/dyalog/dyalog}"
RIDE_PORT="${RIDE_PORT:-4502}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
MOUNT_DIR="$(cd "${MOUNT_DIR:-$REPO_ROOT}" && pwd)"
SELF="${SELF:-$0}"

info() { printf '\033[1;34m==>\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33mwarning:\033[0m %s\n' "$*" >&2; }
die()  { printf '\033[1;31merror:\033[0m %s\n' "$*" >&2; exit 1; }
usage() { sed -n '5,16p' "$SCRIPT_DIR/container.sh" | sed 's/^# \{0,1\}//' | sed "s|./docker.sh|$SELF|"; }

case "$ENGINE" in docker|podman) ;; *) die "ENGINE must be docker or podman" ;; esac

have() { command -v "$1" >/dev/null 2>&1; }

# --- engine setup ------------------------------------------------------------
install_engine() {
  if have "$ENGINE"; then return; fi
  have brew || die "$ENGINE not found and Homebrew isn't installed. See https://brew.sh"
  if [ "$ENGINE" = docker ]; then
    info "Installing Docker Desktop (brew install --cask docker)"
    brew install --cask docker
  else
    info "Installing Podman (brew install podman)"
    brew install podman
  fi
}

engine_running() { "$ENGINE" info >/dev/null 2>&1; }

start_engine() {
  engine_running && return
  if [ "$ENGINE" = podman ]; then
    if [ "$(uname -s)" = Darwin ]; then
      if ! podman machine inspect >/dev/null 2>&1; then
        info "Creating Podman VM (podman machine init)"
        podman machine init
      fi
      info "Starting Podman VM (podman machine start)"
      podman machine start || true
    fi
  else
    if have colima; then
      info "Starting Colima"
      colima start
    elif [ "$(uname -s)" = Darwin ]; then
      info "Starting Docker Desktop"
      open -a Docker
    fi
  fi
  info "Waiting for $ENGINE to be ready..."
  for _ in $(seq 1 60); do engine_running && return; sleep 2; done
  die "$ENGINE isn't responding. Start it manually and try again."
}

# --- image -------------------------------------------------------------------
host_arch() { case "$(uname -m)" in arm64|aarch64) echo arm64 ;; *) echo amd64 ;; esac; }

pull_image() {
  info "Pulling $IMAGE"
  if "$ENGINE" pull "$IMAGE"; then return; fi
  if [ "$(host_arch)" = arm64 ]; then
    warn "No native arm64 image; retrying with --platform linux/amd64 (runs under emulation)"
    "$ENGINE" pull --platform linux/amd64 "$IMAGE" && return
  fi
  die "Couldn't pull $IMAGE"
}

# Add --platform when the local image is amd64 on an arm64 host.
platform_args() {
  local arch
  arch="$("$ENGINE" image inspect --format '{{.Architecture}}' "$IMAGE" 2>/dev/null || true)"
  if [ "$(host_arch)" = arm64 ] && [ "$arch" = amd64 ]; then
    echo "--platform linux/amd64"
  fi
}

ensure_image() {
  "$ENGINE" image inspect "$IMAGE" >/dev/null 2>&1 || pull_image
}

run_container() {
  local extra=("$@") vol="$MOUNT_DIR:/app"
  # SELinux relabel on Linux hosts only.
  if [ "$ENGINE" = podman ] && [ "$(uname -s)" = Linux ]; then vol="$vol:Z"; fi
  # shellcheck disable=SC2046
  exec "$ENGINE" run -it --rm $(platform_args) \
    -v "$vol" -w /app \
    ${extra[@]+"${extra[@]}"} \
    "$IMAGE"
}

# --- commands ----------------------------------------------------------------
case "${1:-}" in
  install)
    install_engine
    start_engine
    pull_image
    info "Ready. Try: $SELF run   or   $SELF ride"
    ;;
  pull)
    have "$ENGINE" || die "$ENGINE not found. Run: $SELF install"
    start_engine
    pull_image
    ;;
  run)
    have "$ENGINE" || die "$ENGINE not found. Run: $SELF install"
    start_engine
    ensure_image
    info "Starting Dyalog ($ENGINE). $MOUNT_DIR is mounted at /app. Exit with )off"
    run_container
    ;;
  ride)
    have "$ENGINE" || die "$ENGINE not found. Run: $SELF install"
    start_engine
    ensure_image
    info "Serving RIDE on localhost:$RIDE_PORT. In RIDE choose Connect -> localhost:$RIDE_PORT"
    run_container -p "$RIDE_PORT:$RIDE_PORT" -e "RIDE_INIT=SERVE:*:$RIDE_PORT"
    ;;
  script)   # script <path-inside-container> [args…]: run an APL script and exit
    [ -n "${2:-}" ] || die "usage: $SELF script /app/file.apls"
    have "$ENGINE" || die "$ENGINE not found. Run: $SELF install"
    start_engine
    ensure_image
    shift
    vol="$MOUNT_DIR:/app"
    if [ "$ENGINE" = podman ] && [ "$(uname -s)" = Linux ]; then vol="$vol:Z"; fi
    tty=(); [ -t 0 ] && [ -t 1 ] && tty=(-t)
    # EXTRA_MOUNT (host:container[:ro]) mounts one more folder, e.g. helpers
    extra=(); [ -n "${EXTRA_MOUNT:-}" ] && extra=(-v "$EXTRA_MOUNT")
    # dyalogscript ends lines with \r\n on a terminal but a bare \r otherwise.
    # Normalise both to \n (awk also adds a missing final newline), and keep
    # dyalogscript's exit code.
    # shellcheck disable=SC2046
    "$ENGINE" run -i ${tty[@]+"${tty[@]}"} --rm $(platform_args) -v "$vol" -w /app \
      ${extra[@]+"${extra[@]}"} --entrypoint dyalogscript "$IMAGE" "$@" \
      | awk '{ sub(/\r$/, ""); gsub(/\r/, "\n"); print }'
    exit "${PIPESTATUS[0]}"
    ;;
  load)     # load <path-inside-container> [LOAD|DYAPP]: session with that file loaded
    [ -n "${2:-}" ] || die "usage: $SELF load /app/MyFn.aplf"
    have "$ENGINE" || die "$ENGINE not found. Run: $SELF install"
    start_engine
    ensure_image
    var="${3:-LOAD}"
    case "$var" in LOAD|DYAPP) ;; *) die "load: variable must be LOAD or DYAPP" ;; esac
    info "Loading $2 (anything set to run at startup runs now). Exit with )off"
    run_container -e "$var=$2"
    ;;
  ""|-h|--help) usage ;;
  *) usage; exit 1 ;;
esac
