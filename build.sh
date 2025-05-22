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

# Create initial superuser if environment variables are set
if [[ $INITIAL_SUPERUSER_USERNAME && $INITIAL_SUPERUSER_PASSWORD ]];
then
  python manage.py create_initial_superuser
fi