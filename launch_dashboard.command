#!/bin/bash

# Change to script directory
cd "$(dirname "$0")"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
  echo "Creating virtual environment..."
  python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install required dependencies
echo "Installing required dependencies..."
pip install pandas numpy

# Run the dashboard server
echo "Starting dashboard server..."
python run_dashboard.py 