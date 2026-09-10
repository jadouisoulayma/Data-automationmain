#!/bin/bash
cd /root/dataAutomation
source venv/bin/activate
exec venv/bin/gunicorn config.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 3 \
    --timeout 300 \
    --access-logfile logs/gunicorn-access.log \
    --error-logfile logs/gunicorn-error.log
