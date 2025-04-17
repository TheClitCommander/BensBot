#!/bin/bash

# Script to run the Portfolio Dashboard
# This automatically activates the virtual environment before running

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"

echo "Activating virtual environment..."
source "$SCRIPT_DIR/venv/bin/activate"

echo "Starting Portfolio Dashboard on http://127.0.0.1:8080"
python3 "$SCRIPT_DIR/portfolio_dashboard.py"

# Note: This script will keep running until you press Ctrl+C
# The virtual environment will remain active after the script ends 