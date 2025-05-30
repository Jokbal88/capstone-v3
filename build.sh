#!/usr/bin/env bash
# exit on error
set -o errexit

# Check if reset flag is provided
if [ "$1" == "--reset-db" ]; then
    echo "Resetting database..."
    chmod +x reset_db.sh
    ./reset_db.sh
    exit 0
fi

# Print Python version
python --version

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Install Node.js dependencies and build Tailwind CSS
echo "Installing Node.js dependencies..."
cd theme
npm install --legacy-peer-deps
npm run build
cd ..

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Run migrations with error handling
echo "Running database migrations..."
python manage.py migrate --noinput || {
    echo "Migration failed. Attempting to fix migration issues..."
    # Try to fake the problematic migration
    python manage.py migrate medical 0020_facultyrequest_is_mental_health_request_and_more --fake
    # Then run the new migration
    python manage.py migrate
}

# Create initial superuser if environment variables are set
if [[ $INITIAL_SUPERUSER_USERNAME && $INITIAL_SUPERUSER_PASSWORD ]]; then
  echo "Creating initial superuser..."
  python manage.py create_initial_superuser
fi

echo "Build completed successfully!"