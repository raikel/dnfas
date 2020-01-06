#!/usr/bin/env bash

PSQL_USER="postgres"
PSQL_PASS=""
DB_NAME="dnfas"
DB_USER="dnfas"
DB_PASS="dnfas"

usage() {
    echo "Usage: $0 -u USER [ -p PASS ] [ -d DB_NAME ] [ -w DB_USER ] [ -q DB_PASS ]" 1>&2
}
exit_abnormal() {                              # Function: Exit with error.
    usage
    exit 1
}

while getopts ":u:p:d:w:q:" options; do
    case "${options}" in
        u)
            PSQL_USER=${OPTARG}
            ;;
        p)
            PSQL_PASS=${OPTARG}
            ;;
        d)
            DB_NAME=${OPTARG}
            ;;
        w)
            DB_USER=${OPTARG}
            ;;
        q)
            DB_PASS=${OPTARG}
            ;;
        :)
            echo "Error: -${OPTARG} requires an argument."
            exit_abnormal
            ;;
        *)
            exit_abnormal
      ;;
    esac
done

export PGPASSWORD=${PSQL_PASS}
psql -U ${PSQL_USER} -h 127.0.0.1 << EOF
    DROP DATABASE IF EXISTS ${DB_NAME};
    CREATE DATABASE ${DB_NAME};
    DROP USER IF EXISTS ${DB_USER};
    CREATE USER ${DB_USER} WITH PASSWORD '${DB_PASS}';
    ALTER ROLE ${DB_USER} SET client_encoding TO 'utf8';
    ALTER ROLE ${DB_USER} SET default_transaction_isolation TO 'read committed';
    ALTER ROLE ${DB_USER} SET timezone TO 'UTC';
    GRANT ALL PRIVILEGES ON DATABASE ${DB_NAME} TO ${DB_USER};
EOF

exit 0