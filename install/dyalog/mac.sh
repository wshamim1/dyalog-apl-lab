#!/usr/bin/env bash
# Set up and run the native macOS Dyalog APL app.
#
# Usage:
#   ./mac.sh install   # check for Dyalog; if missing, open the download page
#   ./mac.sh check     # print the installed app and interpreter path
#   ./mac.sh alias     # add a `dyalog` alias to ~/.zshrc
#   ./mac.sh run       # start an APL session in this terminal
#   ./mac.sh ride      # start the interpreter serving RIDE on port 4502
#
# Env:
#   RIDE_PORT    port for `ride` (default: 4502)

set -euo pipefail

DOWNLOAD_URL="https://www.dyalog.com/download-zone.htm"
RIDE_PORT="${RIDE_PORT:-4502}"

info() { printf '\033[1;34m==>\033[0m %s\n' "$*"; }
die()  { printf '\033[1;31merror:\033[0m %s\n' "$*" >&2; exit 1; }
usage() { sed -n '2,13p' "$0" | sed 's/^# \{0,1\}//'; }

[ "$(uname -s)" = "Darwin" ] || die "This script is for macOS. Use docker.sh or podman.sh instead."

# Newest /Applications/Dyalog-*.app, or empty.
find_app() {
  ls -d /Applications/Dyalog-*.app 2>/dev/null | tail -n 1 || true
}

find_mapl() {
  local app
  app="$(find_app)"
  [ -n "$app" ] && [ -x "$app/Contents/Resources/Dyalog/mapl" ] && echo "$app/Contents/Resources/Dyalog/mapl"
}

require_mapl() {
  MAPL="$(find_mapl || true)"
  [ -n "$MAPL" ] || die "Dyalog not found in /Applications. Run: $0 install"
}

case "${1:-}" in
  install)
    if MAPL="$(find_mapl)"; then
      info "Dyalog is already installed: $(find_app)"
      exit 0
    fi
    info "Dyalog isn't installed. Downloading needs a (free) registration, so this can't be automated."
    info "Opening $DOWNLOAD_URL"
    open "$DOWNLOAD_URL"
    cat <<EOF

  1. Register and download the macOS installer.
  2. Open the .pkg/.dmg and install to /Applications.
  3. If macOS blocks it: System Settings -> Privacy & Security -> Open Anyway.
  4. Run:  $0 check

EOF
    ;;
  check)
    require_mapl
    info "App:         $(find_app)"
    info "Interpreter: $MAPL"
    ;;
  alias)
    require_mapl
    RC="$HOME/.zshrc"
    LINE="alias dyalog='$MAPL'"
    if grep -qs "^alias dyalog=" "$RC"; then
      info "A dyalog alias already exists in $RC. Leaving it unchanged:"
      grep "^alias dyalog=" "$RC"
    else
      printf '\n# Dyalog APL\n%s\n' "$LINE" >> "$RC"
      info "Added to $RC: $LINE"
      info "Run 'source $RC' or open a new terminal."
    fi
    ;;
  run)
    require_mapl
    info "Starting Dyalog (exit with )off)"
    exec "$MAPL"
    ;;
  ride)
    require_mapl
    info "Serving RIDE on localhost:$RIDE_PORT. In RIDE choose Connect -> localhost:$RIDE_PORT"
    RIDE_INIT="SERVE:*:$RIDE_PORT" exec "$MAPL"
    ;;
  ""|-h|--help) usage ;;
  *) usage; exit 1 ;;
esac
