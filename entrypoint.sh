#!/bin/sh

# Exit script in case of error
set -e

# Run database migrations
echo "Running database migrations..."
flask db upgrade

# Start Gunicorn server
echo "Starting Gunicorn server..."
exec gunicorn -w 4 -b 0.0.0.0:8000 "app:create_app()"
