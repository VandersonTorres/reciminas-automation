#!/bin/sh
set -e

cd /app/server

echo "Environment: $ENVIRONMENT"

# wait for PostgreSQL to start if production
if [ "$ENVIRONMENT" = "production" ]; then
  echo "Waiting for PostgreSQL..."

  until nc -z $DB_HOST $DB_PORT; do
    sleep 1
  done
fi

echo "Running migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

# Create superuser if not exists
echo "Creating superuser if not exists..."

python manage.py shell <<EOF
from django.contrib.auth import get_user_model
import os

User = get_user_model()

if not User.objects.filter(is_superuser=True).exists():
    User.objects.create_superuser(
        os.getenv("DJANGO_SUPERUSER_USERNAME"),
        os.getenv("DJANGO_SUPERUSER_EMAIL"),
        os.getenv("DJANGO_SUPERUSER_PASSWORD"),
    )
    print("Superuser created.")
else:
    print("Superuser already exists.")
EOF

# Start the Gunicorn server
echo "Starting Gunicorn server..."
exec gunicorn core.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers 1 \
  --threads 2 \
  --access-logfile - \
  --error-logfile - \
  --log-level info
