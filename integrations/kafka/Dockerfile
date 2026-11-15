# Dyalog APL + the Dyalog Kafka interface (librdkafka), so APL can produce
# and consume Kafka messages. Build: integrations/kafka/build.sh
FROM docker.io/dyalog/dyalog:latest

ARG DYALOG_KAFKA_VERSION=0.1.117
ARG DYALOG_KAFKA_SHA256=d940c49066ae786344fca735e969ba1d95b9bb4e171776f37e9a595bf7172e79

USER root
# libsasl2-2: the one system library librdkafka needs that the Dyalog image lacks.
# The prebuilt library was compiled on a Red Hat-style system, where Cyrus SASL
# 2.1 is named libsasl2.so.3; Debian names the same library libsasl2.so.2, so a
# symlink provides the expected name. (SASL is only used for Kafka logins,
# which the local plaintext broker doesn't need.)
# The release zip is checked against its SHA-256 before anything is unpacked.
RUN apt-get update \
 && apt-get install -y --no-install-recommends libsasl2-2 curl unzip ca-certificates \
 && curl -fsSL -o /tmp/dyalog-kafka.zip \
      "https://github.com/Dyalog/kafka/releases/download/v${DYALOG_KAFKA_VERSION}/dyalog-kafka.linux.${DYALOG_KAFKA_VERSION}.zip" \
 && echo "${DYALOG_KAFKA_SHA256}  /tmp/dyalog-kafka.zip" | sha256sum -c - \
 && mkdir -p /opt/dyalog-kafka \
 && unzip -j /tmp/dyalog-kafka.zip 'linux/x64/64/*' -d /opt/dyalog-kafka \
 && ln -s librdkafka.so /opt/dyalog-kafka/librdkafka.so.1 \
 && ln -s /usr/lib/x86_64-linux-gnu/libsasl2.so.2 /opt/dyalog-kafka/libsasl2.so.3 \
 && rm /tmp/dyalog-kafka.zip \
 && apt-get purge -y curl unzip && apt-get autoremove -y \
 && rm -rf /var/lib/apt/lists/*
# kafka.so links librdkafka.so.1 by name; the loader finds it here
ENV LD_LIBRARY_PATH=/opt/dyalog-kafka
USER dyalog
