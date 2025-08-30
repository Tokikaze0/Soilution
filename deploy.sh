#!/bin/bash

# Deployment script for Django application

echo "Starting deployment..."

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Run database migrations
echo "Running database migrations..."
python manage.py migrate

# Create logs directory
mkdir -p logs

# Set proper permissions
chmod 755 logs

echo "Deployment completed successfully!"
