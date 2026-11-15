#!/usr/bin/env bash
# Run Kafka and APL together in containers.
#
#   kafka.sh up                      start the broker, create the topics
#   kafka.sh run FILE.apls [args]    run an APL script against Kafka
#   kafka.sh processor               live APL stream processor (Ctrl+C to stop)
#   kafka.sh watch TOPIC             print a topic's messages as they arrive
#   kafka.sh topics                  list topics
#   kafka.sh status | down           show / stop the broker
#
# FILE paths are relative to this folder, e.g.  kafka.sh run demo/produce-orders.apls 50
# First time: build the APL image with  ./build.sh
#
# Env: DYALOG_ENGINE (podman|docker), KAFKA_NAME (apl-kafka), KAFKA_NETWORK
#      (apl-kafka), KAFKA_PORT (9092, for clients on your Mac), APL_IMAGE
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../.." && pwd)"
NAME="${KAFKA_NAME:-apl-kafka}"
NET="${KAFKA_NETWORK:-apl-kafka}"
PORT="${KAFKA_PORT:-9092}"
KAFKA_IMAGE="${KAFKA_IMAGE:-docker.io/apache/kafka:3.9.1}"
APL_IMAGE="${APL_IMAGE:-localhost/dyalog-kafka:latest}"
BROKERS="$NAME:19092"          # address for containers on the network
if [ -z "${DYALOG_ENGINE:-}" ]; then
  if command -v podman >/dev/null 2>&1; then DYALOG_ENGINE=podman; else DYALOG_ENGINE=docker; fi
fi
E="$DYALOG_ENGINE"

info() { printf '\033[1;34m==>\033[0m %s\n' "$*"; }
die()  { printf '\033[1;31merror:\033[0m %s\n' "$*" >&2; exit 1; }
running() { [ "$("$E" inspect -f '{{.State.Running}}' "$NAME" 2>/dev/null)" = true ]; }
topics_cmd() { "$E" exec "$NAME" /opt/kafka/bin/kafka-topics.sh --bootstrap-server "$BROKERS" "$@"; }
need_image() { "$E" image inspect "$APL_IMAGE" >/dev/null 2>&1 || die "APL image $APL_IMAGE not found. Run: $HERE/build.sh"; }

case "${1:-}" in
  up)
    "$E" network exists "$NET" 2>/dev/null || "$E" network inspect "$NET" >/dev/null 2>&1 \
      || "$E" network create "$NET" >/dev/null
    if running; then
      info "Kafka is already running ($NAME)"
    else
      "$E" rm -f "$NAME" >/dev/null 2>&1 || true
      info "Starting Kafka ($KAFKA_IMAGE) as $NAME"
      # Two listeners: INTERNAL for containers on the network ($NAME:19092),
      # EXTERNAL for programs on your Mac (localhost:$PORT, this computer only).
      "$E" run -d --name "$NAME" --network "$NET" -p "127.0.0.1:$PORT:9092" \
        -e KAFKA_NODE_ID=1 -e KAFKA_PROCESS_ROLES=broker,controller \
        -e KAFKA_LISTENERS=INTERNAL://:19092,EXTERNAL://:9092,CONTROLLER://:9093 \
        -e "KAFKA_ADVERTISED_LISTENERS=INTERNAL://$NAME:19092,EXTERNAL://localhost:$PORT" \
        -e KAFKA_LISTENER_SECURITY_PROTOCOL_MAP=INTERNAL:PLAINTEXT,EXTERNAL:PLAINTEXT,CONTROLLER:PLAINTEXT \
        -e KAFKA_INTER_BROKER_LISTENER_NAME=INTERNAL -e KAFKA_CONTROLLER_LISTENER_NAMES=CONTROLLER \
        -e KAFKA_CONTROLLER_QUORUM_VOTERS=1@localhost:9093 \
        -e KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR=1 -e KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR=1 \
        -e KAFKA_TRANSACTION_STATE_LOG_MIN_ISR=1 -e KAFKA_GROUP_INITIAL_REBALANCE_DELAY_MS=0 \
        "$KAFKA_IMAGE" >/dev/null
    fi
    info "Waiting for Kafka to be ready…"
    for _ in $(seq 1 60); do topics_cmd --list >/dev/null 2>&1 && break; sleep 1; done
    topics_cmd --list >/dev/null 2>&1 || die "Kafka didn't start. See: $E logs $NAME"
    topics_cmd --create --if-not-exists --topic orders --partitions 3 >/dev/null
    topics_cmd --create --if-not-exists --topic order-stats --partitions 1 >/dev/null
    info "Ready. Topics: $(topics_cmd --list | grep -v '^__' | tr '\n' ' ')"
    echo "   containers use $BROKERS · your Mac uses localhost:$PORT"
    ;;
  run)
    [ -n "${2:-}" ] || die "usage: kafka.sh run FILE.apls [args]"
    running || die "Kafka isn't running. Start it with: kafka.sh up"
    need_image
    f="$2"; shift 2
    [ -f "$HERE/$f" ] || die "no such file: $HERE/$f"
    # dyalogscript ends lines with a bare \r without a terminal; turn into \n
    "$E" run --rm -i --network "$NET" -v "$REPO:/app:ro" -w /app \
      -e "KAFKA_BROKERS=$BROKERS" --entrypoint dyalogscript "$APL_IMAGE" \
      "/app/integrations/kafka/$f" "$@" | awk '{ sub(/\r$/, ""); gsub(/\r/, "\n"); print }'
    exit "${PIPESTATUS[0]}"
    ;;
  processor)
    running || die "Kafka isn't running. Start it with: kafka.sh up"
    need_image
    tty=(-i); [ -t 0 ] && [ -t 1 ] && tty=(-it)
    # A session (not a script) so output appears as it happens
    exec "$E" run "${tty[@]}" --rm --network "$NET" -v "$REPO:/app:ro" -w /app \
      -e "KAFKA_BROKERS=$BROKERS" -e LOAD=/app/integrations/kafka/demo/Pipeline.apln "$APL_IMAGE"
    ;;
  watch)
    [ -n "${2:-}" ] || die "usage: kafka.sh watch TOPIC"
    running || die "Kafka isn't running. Start it with: kafka.sh up"
    exec "$E" exec -it "$NAME" /opt/kafka/bin/kafka-console-consumer.sh \
      --bootstrap-server "$BROKERS" --topic "$2" --from-beginning --property print.key=true
    ;;
  topics) running || die "Kafka isn't running"; topics_cmd --describe | grep -v '^\s*$' ;;
  status) if running; then info "Kafka is running ($NAME, localhost:$PORT)"; else info "Kafka is not running"; fi ;;
  down)
    "$E" rm -f "$NAME" >/dev/null 2>&1 && info "Stopped and removed $NAME (topics and messages are deleted)" || info "Not running"
    ;;
  ""|-h|--help|help) sed -n '2,16p' "$0" | sed 's/^# \{0,1\}//' ;;
  *) die "unknown command '$1' (try: kafka.sh help)" ;;
esac
