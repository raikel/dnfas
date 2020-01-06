#!/usr/bin/env bash

PGUSER=${PGUSER:-"postgres"}
PGPASSWORD=${PGPASSWORD:-""}
DBNAME=${DBNAME:-"dnfas_test"}
DBUSER=${DBUSER:-"dnfas_test"}
DBPASSWORD=${DBPASSWORD:-"dnfas_test"}

export PGPASSWORD=${PGPASSWORD}
psql -U ${PGUSER} -h 127.0.0.1 << EOF
    DROP DATABASE IF EXISTS ${DBNAME};
    CREATE DATABASE ${DBNAME};
    DROP USER IF EXISTS ${DBUSER};
    CREATE USER ${DBUSER} WITH PASSWORD '${DBPASSWORD}';
    ALTER ROLE ${DBUSER} SET client_encoding TO 'utf8';
    ALTER ROLE ${DBUSER} SET default_transaction_isolation TO 'read committed';
    ALTER ROLE ${DBUSER} SET timezone TO 'UTC';
    GRANT ALL PRIVILEGES ON DATABASE ${DBNAME} TO ${DBUSER};
EOF

exit 0