#!/usr/bin/env bash
celery -A dnfas worker -l info -B

# For production
# celery -A proj worker -l info
# celery -A proj beat -l info