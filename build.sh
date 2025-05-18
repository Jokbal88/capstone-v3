#!/usr/bin/env bash
# exit on error
set -o errexit

# Install Python dependencies
pip install -r requirements.txt

# Install Tailwind CSS dependencies
python manage.py tailwind install --no-input

# Build Tailwind CSS
python manage.py tailwind build --no-input

# Collect static files
python manage.py collectstatic --no-input

# Run migrations
python manage.py migrate

if [[ $CREATE_SUPERUSER ]];
then
  python manage.py createsuperuser --no-input --email "$DJANGO_SUPERUSER_EMAIL"
fi