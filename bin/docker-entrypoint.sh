#!/usr/bin/env bash
set -euo pipefail

cd /app

# Django setup
export DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-settings.develop}"

echo "[entrypoint] Applying migrations..."
python manage.py migrate --noinput

echo "[entrypoint] Collecting static..."
python manage.py collectstatic --noinput

echo "[entrypoint] Starting gunicorn..."
cd /app/src
exec gunicorn asgi:application -w ${GUNICORN_WORKERS:-2} -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000 --access-logfile - --error-logfile -

