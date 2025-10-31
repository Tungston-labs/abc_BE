#!/bin/bash
source /var/www/abc_BE/venv/bin/activate
cd /var/www/abc_BE

exec gunicorn ABCBackend.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers 3 \
  --access-logfile /var/www/abc_BE/logs/access.log \
  --error-logfile /var/www/abc_BE/logs/error.log

