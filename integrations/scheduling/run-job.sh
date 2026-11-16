#!/usr/bin/env bash
# Run any APL script as an unattended job: safe to call from cron, launchd,
# CI or another scheduler.
#
#   run-job.sh FILE.apls [args…]
#
# FILE is relative to the repo root (or absolute, inside the repo), e.g.
#   run-job.sh integrations/scheduling/job/daily-report.apls
#   run-job.sh sample-scripts/10-csv-report.apls
#
# What it adds on top of `dyalog FILE.apls`:
#   - works with cron's bare environment (sets PATH, uses absolute paths)
#   - one log file per run in output/logs/, plus <job>-latest.log
#   - a lock, so a slow run and the next scheduled one never overlap
#   - the script's exit code is passed back (0 = ok), so the scheduler can
#     tell a failure from a success; logs older than KEEP_LOG_DAYS are deleted
#
# Env: JOB_LOG_DIR (default: integrations/scheduling/output/logs),
#      KEEP_LOG_DAYS (14), DYALOG_ENGINE (podman|docker), LOG_LEVEL
set -uo pipefail

# cron starts jobs with PATH=/usr/bin:/bin; podman/docker live elsewhere.
export PATH="/usr/local/bin:/opt/homebrew/bin:$PATH"

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../.." && pwd)"
LOG_DIR="${JOB_LOG_DIR:-$HERE/output/logs}"
KEEP="${KEEP_LOG_DAYS:-14}"

die() { echo "run-job: $*" >&2; exit 2; }
[ -n "${1:-}" ] || die "usage: run-job.sh FILE.apls [args…]"
file="$1"; shift
case "$file" in /*) ;; *) file="$REPO/$file" ;; esac
[ -f "$file" ] || die "no such file: $file"
case "$file" in "$REPO"/*) ;; *) die "$file is outside the repo ($REPO)" ;; esac
job="$(basename "$file" .apls)"

mkdir -p "$LOG_DIR" || die "can't create $LOG_DIR"
stamp="$(date +%Y%m%d-%H%M%S)"
log="$LOG_DIR/$job-$stamp.log"

# Lock: mkdir is atomic. If the lock is left over from a run that was killed,
# its PID is no longer alive, so take it over.
lock="$LOG_DIR/.$job.lock"
if ! mkdir "$lock" 2>/dev/null; then
  pid="$(cat "$lock/pid" 2>/dev/null || true)"
  if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
    echo "$(date '+%F %T') SKIP  $job: still running (pid $pid)" | tee -a "$LOG_DIR/$job-skipped.log" >&2
    exit 0      # not a failure: the earlier run is still doing the work
  fi
  rm -rf "$lock"; mkdir "$lock" || die "can't take lock $lock"
fi
echo $$ > "$lock/pid"
trap 'rm -rf "$lock"' EXIT

(
  echo "== $job · start $(date '+%F %T') · $file $*"
  cd "$REPO" && "$REPO/install/dyalog/dyalog" "${file#"$REPO"/}" "$@" </dev/null
  code=$?
  echo "== $job · end $(date '+%F %T') · exit $code"
  exit $code
) >"$log" 2>&1
code=$?

ln -sf "$(basename "$log")" "$LOG_DIR/$job-latest.log"
find "$LOG_DIR" -name "$job-2*.log" -mtime +"$KEEP" -delete 2>/dev/null || true

if [ $code -ne 0 ]; then
  # stderr: cron mails it to you (if mail is set up); other schedulers show it
  echo "run-job: $job failed with exit $code. Log: $log" >&2
  tail -n 20 "$log" >&2
fi
exit $code
