#!/bin/bash

# Setup script for Calendarium dev container
echo "Setting up Calendarium development environment..."

# Create symbolic link to /app
echo "Creating symbolic link to /app..."
sudo ln -s $(pwd) /app

# Create data directory
echo "Creating data directory..."
sudo mkdir -p /app/data

# Install Python dependencies
echo "Installing Python dependencies..."
pip3 install --user -r requirements.txt

# Install pytest for testing
echo "Installing pytest..."
pip3 install --user pytest

echo "Setup complete! Ready to go!"
echo "Navigate to your project directory and run 'flask run' to start your application."
