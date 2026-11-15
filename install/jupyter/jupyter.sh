#!/usr/bin/env bash
# JupyterLab with Dyalog APL, in a container.
#
#   jupyter.sh start [port]     open JupyterLab on this computer (default 8888)
#   jupyter.sh execute [files]  run notebooks headlessly and save their outputs
#                               (default: notebooks/[0-9]*.ipynb)
#   jupyter.sh fetch-dyalog     download Dyalog's 44 ready-made notebooks
#                               into notebooks/dyalog/ (not committed)
#   jupyter.sh build            build the image (localhost/dyalog-jupyter)
#
# The repo is mounted at /app (read-write, so notebooks save), and JupyterLab
# opens in notebooks/. Code can be loaded with ]load /app/…, as in the tutorials.
#
# Env: DYALOG_ENGINE (podman|docker), JUPYTER_IMAGE
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../.." && pwd)"
IMAGE="${JUPYTER_IMAGE:-localhost/dyalog-jupyter:latest}"
# Dyalog's notebooks, pinned to a known commit
DYALOG_NB_REPO="Dyalog/dyalog-jupyter-notebooks"
DYALOG_NB_REF="${DYALOG_NB_REF:-master}"
if [ -z "${DYALOG_ENGINE:-}" ]; then
  if command -v podman >/dev/null 2>&1; then DYALOG_ENGINE=podman; else DYALOG_ENGINE=docker; fi
fi
E="$DYALOG_ENGINE"

info() { printf '\033[1;34m==>\033[0m %s\n' "$*"; }
die()  { printf '\033[1;31merror:\033[0m %s\n' "$*" >&2; exit 1; }
need_image() { "$E" image inspect "$IMAGE" >/dev/null 2>&1 || die "Image $IMAGE not found. Run: $0 build"; }

case "${1:-}" in
  build)
    ENGINE="$E" IMAGE="$IMAGE" exec "$HERE/build.sh"
    ;;
  start)
    need_image
    PORT="${2:-8888}"
    tty=(-i); [ -t 0 ] && [ -t 1 ] && tty=(-it)
    info "Starting JupyterLab. Open the http://127.0.0.1:$PORT/lab?token=… link it prints."
    info "Notebooks: $REPO/notebooks   ·   Stop: Ctrl+C"
    # Only this computer can connect (127.0.0.1). Jupyter's token protects it too.
    exec "$E" run "${tty[@]}" --rm -p "127.0.0.1:$PORT:8888" -v "$REPO:/app" "$IMAGE" \
      lab --ip=0.0.0.0 --port=8888 --no-browser --notebook-dir=/app/notebooks \
      --ServerApp.custom_display_url="http://127.0.0.1:$PORT/lab"
    ;;
  execute)
    need_image
    shift
    if [ $# -eq 0 ]; then
      set -- "$REPO"/notebooks/[0-9]*.ipynb
    fi
    files=()
    for f in "$@"; do
      abs="$(cd "$(dirname "$f")" && pwd)/$(basename "$f")"
      case "$abs" in "$REPO"/*) files+=("/app/${abs#"$REPO"/}") ;; *) die "$f is not inside the repo" ;; esac
    done
    info "Running ${#files[@]} notebook(s) in Dyalog…"
    # Cells tagged raises-exception may fail on purpose; any other error stops the run.
    "$E" run --rm -v "$REPO:/app" --entrypoint jupyter "$IMAGE" \
      nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=120 "${files[@]}"
    info "Done: outputs saved in the notebooks."
    ;;
  fetch-dyalog)
    dest="$REPO/notebooks/dyalog"
    command -v curl >/dev/null || die "curl is needed"
    tmp="$(mktemp -d)"
    info "Downloading $DYALOG_NB_REPO ($DYALOG_NB_REF)…"
    curl -fsSL "https://codeload.github.com/$DYALOG_NB_REPO/tar.gz/$DYALOG_NB_REF" -o "$tmp/nb.tar.gz"
    mkdir -p "$dest"
    tar -xzf "$tmp/nb.tar.gz" -C "$dest" --strip-components=1
    rm -f "$tmp/nb.tar.gz"; rmdir "$tmp"
    info "$(find "$dest" -name '*.ipynb' | wc -l | tr -d ' ') notebooks in notebooks/dyalog/ (MIT licence: notebooks/dyalog/LICENSE)"
    ;;
  ""|-h|--help|help) sed -n '2,14p' "$0" | sed 's/^# \{0,1\}//' ;;
  *) die "unknown command '$1' (try: jupyter.sh help)" ;;
esac
