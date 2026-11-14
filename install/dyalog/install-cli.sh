#!/usr/bin/env bash
# Install the `dyalog` command (a link to install/dyalog/dyalog).
#
#   install/dyalog/install-cli.sh             # link into /usr/local/bin (or ~/.local/bin)
#   install/dyalog/install-cli.sh --uninstall
#
# It replaces an existing `dyalog` only if that is a broken link or already
# points here. A working native Dyalog install is left alone.

set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET="$HERE/dyalog"

info() { printf '\033[1;34m==>\033[0m %s\n' "$*"; }
die()  { printf '\033[1;31merror:\033[0m %s\n' "$*" >&2; exit 1; }

# Pick the first writable bin directory on PATH, preferring /usr/local/bin.
pick_dir() {
  for d in /usr/local/bin "$HOME/.local/bin"; do
    if [ -d "$d" ] && [ -w "$d" ] && [[ ":$PATH:" == *":$d:"* ]]; then
      echo "$d"; return
    fi
  done
  die "No writable bin directory on PATH (tried /usr/local/bin, ~/.local/bin)."
}

DIR="$(pick_dir)"
LINK="$DIR/dyalog"

if [ "${1:-}" = "--uninstall" ]; then
  if [ -L "$LINK" ] && [ "$(readlink "$LINK")" = "$TARGET" ]; then
    rm "$LINK" && info "Removed $LINK"
  else
    info "Nothing to remove ($LINK isn't our link)."
  fi
  exit 0
fi

if [ -e "$LINK" ] || [ -L "$LINK" ]; then
  if [ -L "$LINK" ] && [ "$(readlink "$LINK")" = "$TARGET" ]; then
    info "Already installed: $LINK -> $TARGET"
    exit 0
  elif [ -L "$LINK" ] && [ ! -e "$LINK" ]; then
    info "Replacing broken link $LINK -> $(readlink "$LINK")"
    rm "$LINK"
  else
    die "$LINK already exists and works ($(readlink "$LINK" 2>/dev/null || echo file)). Remove it first if you want to replace it."
  fi
fi

chmod +x "$TARGET" "$HERE/container.sh"
ln -s "$TARGET" "$LINK"
info "Installed: $LINK -> $TARGET"
hash -r 2>/dev/null || true
echo
echo "Try:  dyalog          (APL in this terminal; Ctrl+D or )off to quit)"
echo "      dyalog ride     (then connect RIDE to localhost:4502)"
