#!/usr/bin/env bash
# Local Airflow that runs APL scripts.
#
#   airflow.sh up                 build the image (first time) and start Airflow
#   airflow.sh trigger DAG [CONF] run a DAG now and wait for it to finish
#   airflow.sh status             containers, and the last runs of each APL DAG
#   airflow.sh logs               follow Airflow's own log
#   airflow.sh build              rebuild the image (after changing the Dockerfile)
#   airflow.sh down               stop (keeps the database: run history survives)
#   airflow.sh reset              stop and delete the database and logs
#
# DAGs: apl_daily_report, apl_sample_scripts. UI: http://localhost:8088
# Env: DYALOG_ENGINE (podman|docker), AIRFLOW_PORT (8088)
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PORT="${AIRFLOW_PORT:-8088}"
IMAGE=localhost/apl-airflow:latest
if [ -z "${DYALOG_ENGINE:-}" ]; then
  if command -v podman >/dev/null 2>&1; then DYALOG_ENGINE=podman; else DYALOG_ENGINE=docker; fi
fi
E="$DYALOG_ENGINE"

info() { printf '\033[1;34m==>\033[0m %s\n' "$*"; }
die()  { printf '\033[1;31merror:\033[0m %s\n' "$*" >&2; exit 1; }
# podman compose hands over to docker-compose or podman-compose; hide its banner
compose() { "$E" compose -f "$HERE/docker-compose.yaml" "$@" 2> >(grep -v -e 'Executing external compose provider' -e 'podman-compose(1)' -e '^$' >&2); }
af() { "$E" exec apl-airflow-airflow-1 airflow "$@" 2> >(grep -v -e DeprecatedImportWarning -e 'warnings.warn' >&2); }
healthy() { [ "$("$E" inspect -f '{{.State.Health.Status}}' apl-airflow-airflow-1 2>/dev/null)" = healthy ]; }
need_up() { healthy || die "Airflow isn't running (or is still starting). Start it with: airflow.sh up"; }

build() { info "Building $IMAGE (Airflow + Dyalog)"; "$E" build -t "$IMAGE" "$HERE"; }

case "${1:-}" in
  up)
    command -v "$E" >/dev/null || die "$E not found. Run: install/dyalog/dyalog setup"
    "$E" image inspect "$IMAGE" >/dev/null 2>&1 || build
    mkdir -p "$HERE/../output/reports"
    info "Starting Airflow (postgres + airflow standalone)"
    compose up -d --no-build
    info "Waiting for Airflow to be ready (first start sets up the database: ~1 min)…"
    for _ in $(seq 1 90); do healthy && break; sleep 2; done
    healthy || die "Airflow didn't become healthy. See: airflow.sh logs"
    info "Ready: http://localhost:$PORT  (no login: local use only)"
    echo "   Try:  $0 trigger apl_daily_report"
    ;;
  trigger)
    dag="${2:-}"; [ -n "$dag" ] || die "usage: airflow.sh trigger DAG [CONF-JSON]"
    need_up
    # a new DAG file can take a few seconds to be picked up
    for _ in $(seq 1 15); do af dags details "$dag" >/dev/null 2>&1 && break; sleep 2; done
    af dags details "$dag" >/dev/null 2>&1 || die "no DAG named $dag. DAGs: $(af dags list -o plain 2>/dev/null | awk 'NR>1{print $1}' | tr '\n' ' ')"
    af dags unpause "$dag" >/dev/null
    run_id="manual__$(date -u +%Y-%m-%dT%H:%M:%S)"
    af dags trigger "$dag" --run-id "$run_id" ${3:+--conf "$3"} >/dev/null
    info "Triggered $dag ($run_id); waiting…"
    state=""; end=$((SECONDS + 300))
    while [ $SECONDS -lt $end ]; do
      state="$(af dags list-runs "$dag" -o json 2>/dev/null \
        | python3 -c "import json,sys; print(next((r['state'] for r in json.load(sys.stdin) if r['run_id']=='$run_id'),''))" 2>/dev/null || true)"
      case "$state" in success|failed) break ;; esac
      sleep 2
    done
    af tasks states-for-dag-run "$dag" "$run_id" -o table 2>/dev/null || true
    case "$state" in
      success) info "$dag: success. Logs: http://localhost:$PORT/dags/$dag" ;;
      failed)  die "$dag: failed. Open http://localhost:$PORT/dags/$dag and click the red task for its log" ;;
      *)       die "$dag: still ${state:-queued} after 5 minutes. Check http://localhost:$PORT/dags/$dag" ;;
    esac
    ;;
  status)
    compose ps
    if healthy; then
      for d in apl_daily_report apl_sample_scripts; do
        echo; echo "$d (latest runs):"
        af dags list-runs "$d" -o plain 2>/dev/null | head -6 || true
      done
    fi
    ;;
  logs)  compose logs -f airflow ;;
  build) build ;;
  down)  compose down; info "Stopped. Run history is kept; airflow.sh reset deletes it." ;;
  reset) compose down -v; info "Stopped and deleted the database and logs." ;;
  ""|-h|--help) sed -n '2,13p' "$0" | sed 's/^# \{0,1\}//' ;;
  *) die "unknown command '$1' (try: airflow.sh help)" ;;
esac
