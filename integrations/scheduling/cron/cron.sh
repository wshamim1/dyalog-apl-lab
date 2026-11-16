#!/usr/bin/env bash
# Schedule APL scripts with cron.
#
#   cron.sh add "SCHEDULE" FILE.apls [args…]   add a crontab line for FILE
#   cron.sh list                               show the APL jobs in your crontab
#   cron.sh remove [JOB]                       remove one job (by name), or all of them
#   cron.sh test FILE.apls [args…]             run FILE now, the way cron would
#
# FILE is relative to the repo root. SCHEDULE is the usual five cron fields:
#   cron.sh add "0 6 * * *"   integrations/scheduling/job/daily-report.apls   # 06:00 daily
#   cron.sh add "*/15 * * * *" sample-scripts/04-primes.apls                  # every 15 min
#
# Each line is tagged "# apl-job:<name>", so list and remove touch only the
# lines this script added and leave the rest of your crontab alone.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../../.." && pwd)"
RUN="$REPO/integrations/scheduling/run-job.sh"
TAG="# apl-job:"

info() { printf '\033[1;34m==>\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33mwarning:\033[0m %s\n' "$*" >&2; }
die()  { printf '\033[1;31merror:\033[0m %s\n' "$*" >&2; exit 1; }
current() { crontab -l 2>/dev/null || true; }
# Lines tagged exactly "# apl-job:JOB" (so daily-report doesn't match daily-report2)
tagged()   { awk -v t="$TAG$1" 'substr($0, length($0)-length(t)+1) == t'; }
untagged() { awk -v t="$TAG$1" 'substr($0, length($0)-length(t)+1) != t'; }
check_file() { [ -f "$REPO/$1" ] || die "no such file: $REPO/$1 (give a path relative to the repo root)"; }

# macOS keeps cron out of Desktop, Documents and Downloads unless cron has
# Full Disk Access; the job then fails with "Operation not permitted".
mac_privacy_warning() {
  [ "$(uname -s)" = Darwin ] || return 0
  case "$REPO" in
    "$HOME"/Desktop/*|"$HOME"/Documents/*|"$HOME"/Downloads/*)
      warn "the repo is in a folder macOS protects ($REPO)."
      echo "   Give cron Full Disk Access: System Settings → Privacy & Security → Full Disk Access" >&2
      echo "   → + → press ⌘⇧G, type /usr/sbin/cron → Open. Or move the repo outside Desktop/Documents/Downloads." >&2 ;;
  esac
}

# Quote one argument for the crontab line. % means "newline" to cron, so escape it.
q() { printf '%q' "$1" | sed 's/%/\\%/g'; }

case "${1:-}" in
  add)
    [ $# -ge 3 ] || die 'usage: cron.sh add "SCHEDULE" FILE.apls [args…]'
    sched="$2"; file="$3"; shift 3
    [ "$(echo "$sched" | wc -w)" -eq 5 ] || die "SCHEDULE needs 5 fields, e.g. \"0 6 * * *\" (got: $sched)"
    check_file "$file"
    job="$(basename "$file" .apls)"
    before="$(current)"     # read it all first: crontab - may replace it while we read
    [ -n "$(echo "$before" | tagged "$job")" ] && die "a job named $job is already scheduled. Remove it first: cron.sh remove $job"
    cmd="$(q "$RUN") $(q "$file")"
    for a in "$@"; do cmd="$cmd $(q "$a")"; done
    # run-job.sh writes its own logs; cron's copy of the output goes nowhere.
    line="$sched $cmd >/dev/null 2>&1 $TAG$job"
    { [ -n "$before" ] && echo "$before"; echo "$line"; } | crontab -
    info "Added: $line"
    echo "   Logs: integrations/scheduling/output/logs/$job-latest.log"
    mac_privacy_warning
    ;;
  list)
    current | grep -F "$TAG" || echo "(no APL jobs in your crontab)"
    ;;
  remove)
    job="${2:-}"
    before="$(current)"
    if [ -n "$job" ]; then
      [ -n "$(echo "$before" | tagged "$job")" ] || die "no job named $job (see: cron.sh list)"
      after="$(echo "$before" | untagged "$job")"
    else
      after="$(echo "$before" | grep -vF "$TAG" || true)"
    fi
    if [ -z "$after" ]; then crontab -r 2>/dev/null || true; else echo "$after" | crontab -; fi
    info "Removed ${job:-all APL jobs}"
    ;;
  test)
    [ $# -ge 2 ] || die "usage: cron.sh test FILE.apls [args…]"
    check_file "$2"; shift
    # cron's environment: almost nothing set, PATH=/usr/bin:/bin, no terminal
    info "Running as cron would (empty environment, no terminal)"
    set +e
    env -i HOME="$HOME" LOGNAME="${LOGNAME:-$USER}" USER="$USER" SHELL=/bin/sh PATH=/usr/bin:/bin \
      "$RUN" "$@" </dev/null
    code=$?
    set -e
    job="$(basename "$1" .apls)"
    info "exit $code · log: integrations/scheduling/output/logs/$job-latest.log"
    exit $code
    ;;
  ""|-h|--help) sed -n '2,15p' "$0" | sed 's/^# \{0,1\}//' ;;
  *) die "unknown command '$1' (try: cron.sh help)" ;;
esac
