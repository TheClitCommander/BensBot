#!/bin/bash

# Change to script directory
cd "$(dirname "$0")"

echo "===================================="
echo "BenBot Chat with API Key Fix"
echo "===================================="
echo ""
echo "This script will properly load API keys and run the dashboard server."
echo ""

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
  echo "Creating virtual environment..."
  python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install required dependencies
echo "Installing required dependencies..."
pip install pandas numpy python-dotenv

# Kill any existing dashboard processes
echo "Stopping any existing dashboard processes..."
pkill -f "python run_dashboard.py" || true
pkill -f "python run_with_api_keys.py" || true

# Add execute permission to the Python script
chmod +x run_with_api_keys.py

# Run our special API key loader script
echo ""
echo "Starting the dashboard with API keys properly loaded..."
echo "Press Ctrl+C to stop the server when done."
echo ""

python run_with_api_keys.py 