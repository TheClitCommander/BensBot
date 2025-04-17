#!/bin/bash

# Change to the directory where this script is located
cd "$(dirname "$0")"

# Activate virtual environment
source venv/bin/activate

# Clear terminal
clear

# Print status message
echo "--------------------------------------------------------"
echo "Starting Trading Bot Dashboard with Streamlit..."
echo "--------------------------------------------------------"
echo "When ready, access the dashboard at: http://localhost:8080"
echo "Press Ctrl+C to stop the server"
echo "--------------------------------------------------------"

# Install streamlit if needed
pip install streamlit --quiet

# Run the dashboard application using streamlit
python streamlit_run.py

# Keep terminal window open after script exits so errors can be viewed
echo "--------------------------------------------------------"
echo "Dashboard server has stopped. Press any key to close this window."
echo "--------------------------------------------------------"
read -n 1 -s 