#!/usr/bin/env bash
# Clone (or update) RIDE from source and build it.
#
# Usage:
#   ./install.sh            # clone/update, install deps, compile css
#   ./install.sh --start    # ...then start RIDE
#   ./install.sh --build    # ...then build a native app under ride/_/
#
# Env:
#   RIDE_DIR   where to put the source (default: <this folder>/ride)
#   RIDE_REF   branch or tag to check out (default: repo default branch)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RIDE_DIR="${RIDE_DIR:-$SCRIPT_DIR/ride}"
RIDE_REPO="https://github.com/dyalog/ride"
WANT_NODE="18.17.0"

ACTION=""
case "${1:-}" in
  --start) ACTION=start ;;
  --build) ACTION=build ;;
  "") ;;
  -h|--help) sed -n '2,11p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
  *) echo "Unknown option: $1 (try --help)" >&2; exit 1 ;;
esac

info() { printf '\033[1;34m==>\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33mwarning:\033[0m %s\n' "$*" >&2; }
die()  { printf '\033[1;31merror:\033[0m %s\n' "$*" >&2; exit 1; }

# --- prerequisites -----------------------------------------------------------
command -v git >/dev/null || die "git not found. Install it with: xcode-select --install"

# Use nvm to switch to the recommended Node version if it's available.
NVM_SH=""
for f in "${NVM_DIR:-$HOME/.nvm}/nvm.sh" "$(brew --prefix nvm 2>/dev/null || true)/nvm.sh"; do
  if [ -s "$f" ]; then NVM_SH="$f"; break; fi
done
if [ -n "$NVM_SH" ]; then
  export NVM_DIR="${NVM_DIR:-$HOME/.nvm}"
  set +u   # nvm isn't safe under `set -u`
  # shellcheck disable=SC1090
  . "$NVM_SH"
  info "Switching to Node $WANT_NODE with nvm"
  nvm install "$WANT_NODE" >/dev/null && nvm use "$WANT_NODE" >/dev/null || warn "nvm couldn't switch to $WANT_NODE"
  set -u
fi

command -v node >/dev/null || die "node not found. Install Node $WANT_NODE (e.g. via nvm)."
command -v npm  >/dev/null || die "npm not found."

NODE_VER="$(node -v | sed 's/^v//')"
if [ "$NODE_VER" != "$WANT_NODE" ]; then
  warn "Using Node $NODE_VER; RIDE documents $WANT_NODE. If the build fails, run: nvm install $WANT_NODE && nvm use $WANT_NODE"
fi

# --- clone or update ---------------------------------------------------------
if [ -d "$RIDE_DIR/.git" ]; then
  info "Updating RIDE in $RIDE_DIR"
  git -C "$RIDE_DIR" pull --ff-only
else
  info "Cloning RIDE into $RIDE_DIR"
  git clone --depth=1 ${RIDE_REF:+--branch "$RIDE_REF"} "$RIDE_REPO" "$RIDE_DIR"
fi

cd "$RIDE_DIR"

# --- build -------------------------------------------------------------------
info "Installing dependencies (npm i)"
npm i

info "Compiling CSS (npm run css)"
npm run css

case "$ACTION" in
  start)
    info "Starting RIDE"
    npm start
    ;;
  build)
    info "Building native app (npm run build dist)"
    npm run build dist
    info "Build output is in $RIDE_DIR/_/"
    ;;
  *)
    info "Done. Start RIDE with:  cd \"$RIDE_DIR\" && npm start"
    ;;
esac
