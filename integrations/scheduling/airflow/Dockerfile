# Apache Airflow with Dyalog APL inside it, so a task can run an APL script
# directly:  apl-run /apl/path/to/job.apls args…
# Build and start: integrations/scheduling/airflow/airflow.sh up
#
# Dyalog is copied out of the official Dyalog image. Both images are Debian 13,
# and the interpreter only needs libc and libm, so nothing else has to be
# installed.
ARG AIRFLOW_IMAGE=docker.io/apache/airflow:3.4.0-python3.12
ARG DYALOG_IMAGE=docker.io/dyalog/dyalog:latest

FROM ${DYALOG_IMAGE} AS dyalog

FROM ${AIRFLOW_IMAGE}
USER root
COPY --from=dyalog /opt/mdyalog /opt/mdyalog
COPY apl-run /usr/local/bin/apl-run
RUN v="$(ls /opt/mdyalog)" \
 && ln -s "/opt/mdyalog/$v/64/unicode/dyalog" /usr/local/bin/dyalog \
 && ln -s "/opt/mdyalog/$v/64/unicode/scriptbin/dyalogscript" /usr/local/bin/dyalogscript \
 && chmod 755 /usr/local/bin/apl-run \
 # scripts load the shared library from /apl-lib, as with the `dyalog` command
 && ln -s /apl/lib /apl-lib \
 # check that the interpreter runs here (grep fails the build if it printed nothing)
 && echo "⎕←'Dyalog ',2⊃'.' ⎕WG'APLVersion'" > /tmp/v.apls \
 && ENABLE_CEF=0 dyalogscript /tmp/v.apls </dev/null | tr '\r' '\n' | grep '^Dyalog [0-9]' \
 && rm /tmp/v.apls
# ENABLE_CEF=0: no HTML renderer (there's no display). APL_LIB: the shared
# library (/apl-lib → /apl/lib, the repo docker-compose.yaml mounts at /apl).
ENV ENABLE_CEF=0 \
    APL_LIB=/apl-lib/Lib.apln
USER airflow
