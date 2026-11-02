#!/bin/sh
echo ""
cat /opt/application/webapp/RELEASE
echo "------------------------------------------------"
echo "DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE}"
echo "DJANGO_ALLOWED_HOSTS=${DJANGO_ALLOWED_HOSTS}"
echo "DJANGO_BIND_HOST=${DJANGO_BIND_HOST}"
echo "------------------------------------------------"
echo "Waiting for database ${MYSQL_USER}@${MYSQL_HOST}:${MYSQL_PORT}..."

# Use nc to check if the MySQL service is ready
# Ensure MYSQL_HOST and MYSQL_PORT are correctly passed as environment variables to the web service
# The -z flag is for zero-I/O mode (for scanning)
# The -w 1 flag sets a timeout of 1 second for the connection
until nc -z -w 1 ${MYSQL_HOST} ${MYSQL_PORT}; do
  echo "MySQL not ready yet. Retrying in 2s..." # Increased sleep to 2s
  sleep 2
done
echo "Database ok"

# Collect static files
echo "Collect static files..."
poetry run python manage.py collectstatic --no-input --clear --settings=base.settings.docker
ls -al /opt/application/webapp/staticfiles

# Migrate database
echo "Migrate database..."
poetry run python manage.py migrate --settings=base.settings.docker # Explicitly use the docker settings
# Add initial data load if you have fixtures or a seed script
# poetry run python manage.py loaddata initial_data.json # Example for loading fixtures

# Run Gunicorn
echo "Starting Gunicorn..."
.venv/bin/gunicorn base.wsgi:application --bind ${DJANGO_BIND_HOST} --workers=3 --threads=4 --worker-class=gthread --worker-tmp-dir /dev/shm
