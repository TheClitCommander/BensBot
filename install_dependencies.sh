#!/bin/bash
# Script to install dependencies for the Trading Dashboard

echo "Installing required dependencies..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install streamlit pandas numpy plotly
pip install python-socketio websockets alpaca-trade-api
pip install requests

echo "Installation complete!"
echo "You can now run the app with: ./run_streamlit_app.sh" 