# Dyalog APL + MariaDB ODBC driver, so APL can reach MySQL/MariaDB through
# SQAPL (Dyalog's built-in ODBC interface, ws/sqapl.dws).
FROM docker.io/dyalog/dyalog:latest

USER root
RUN apt-get update \
 && apt-get install -y --no-install-recommends odbc-mariadb \
 && rm -rf /var/lib/apt/lists/*
USER dyalog
