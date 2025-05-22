#!/usr/bin/env bash
# exit on error
set -o errexit

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn

# Install Node.js dependencies and build Tailwind CSS
cd theme
npm install --legacy-peer-deps
npm run build
cd ..

# Collect static files
python manage.py collectstatic --no-input

# Run migrations
python manage.py migrate

if [[ $CREATE_SUPERUSER ]];
then
  python manage.py createsuperuser --no-input --username "$DJANGO_SUPERUSER_USERNAME" --email "$DJANGO_SUPERUSER_EMAIL"
fi