#!/usr/bin/env bash
bash dbinit.sh -u ${PGUSER} -p ${PGPASSWORD} -d dnfas_test -w dnfas_test -q dnfas_test
coverage run --rcfile=.coveragerc manage.py test --keepdb