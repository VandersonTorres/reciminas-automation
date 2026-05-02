#!/bin/sh
set -e

cd /app/server

echo "Running migrations..."
python manage.py migrate --noinput

# Start the Gunicorn server
echo "Starting Gunicorn server..."
exec gunicorn core.wsgi:application --bind 0.0.0.0:8000 --workers 1 --threads 2
