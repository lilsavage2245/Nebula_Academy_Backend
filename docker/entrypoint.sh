#!/usr/bin/env bash
set -e

export DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE:-config.settings}

echo "Running migrations..."
python manage.py migrate --noinput

echo "Collecting static..."
python manage.py collectstatic --noinput || true

echo "Starting gunicorn..."
exec gunicorn config.wsgi:application \
  --bind 0.0.0.0:${PORT:-8000} \
  --workers 3 \
  --timeout 120 \
  --log-file -
