#!/bin/bash

# Change to the directory where this script is located
cd "$(dirname "$0")"

# Activate virtual environment
source venv/bin/activate

# Clear terminal
clear

# Print status message
echo "--------------------------------------------------------"
echo "Starting Trading Bot Dashboard on port 8080..."
echo "--------------------------------------------------------"
echo "When ready, access the dashboard at: http://localhost:8080"
echo "Press Ctrl+C to stop the server"
echo "--------------------------------------------------------"

# Run the dashboard application directly with port specified
cd trading_bot/dashboard
python -c "
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath('__file__')))
import app
app.socketio.run(app.app, debug=True, host='0.0.0.0', port=8080)
"

# Keep terminal window open after script exits so errors can be viewed
echo "--------------------------------------------------------"
echo "Dashboard server has stopped. Press any key to close this window."
echo "--------------------------------------------------------"
read -n 1 -s 