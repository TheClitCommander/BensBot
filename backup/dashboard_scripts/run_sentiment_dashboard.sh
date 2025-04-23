#!/bin/bash

# Run BenBot Homepage Dashboard
# This script runs the main dashboard application

echo "========================================"
echo "           BenBot Homepage             "
echo "========================================"

# Activate virtual environment
if [ -d "trading_env" ]; then
    echo "Activating trading environment..."
    source trading_env/bin/activate
else
    echo "Error: trading_env directory not found."
    echo "Please run the installation script first."
    exit 1
fi

# Install requirements if needed
if [ -f "requirements.txt" ]; then
    echo "Checking requirements..."
    pip install -r requirements.txt > /dev/null
fi

# Run the application
echo "Starting dashboard... (press Ctrl+C to stop)"
echo "========================================"
streamlit run app.py 