#!/bin/bash

# Navigate to the project directory
cd "$(dirname "$0")"

# Clear the terminal
clear

# Display header
echo "=========================================="
echo "       BENBOT DASHBOARD LAUNCHER         "
echo "=========================================="
echo ""

# Ensure simple_dashboard.py is executable
chmod +x simple_dashboard.py

# Run the dashboard
echo "Starting the dashboard..."
echo "The browser should open automatically."
echo "Press Ctrl+C to stop the dashboard when finished."
echo ""

# Run the script
python3 simple_dashboard.py

# Keep terminal window open
echo ""
echo "Dashboard stopped. Press any key to close this window."
read -n 1 