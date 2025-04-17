#!/bin/bash

# Script to set up the Portfolio Dashboard environment
# This creates a virtual environment and installs the required dependencies

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"

echo "Creating virtual environment in $SCRIPT_DIR/venv..."
python3 -m venv "$SCRIPT_DIR/venv"

echo "Activating virtual environment..."
source "$SCRIPT_DIR/venv/bin/activate"

echo "Installing required packages..."
pip install Flask

echo ""
echo "Setup complete! You can now run the dashboard with:"
echo "./run_dashboard.sh"
echo ""
echo "Or access it directly in your browser at:"
echo "http://127.0.0.1:8080" 