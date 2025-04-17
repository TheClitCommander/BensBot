#!/bin/bash

# VERBOSE DEBUG LAUNCHER FOR TRADING DASHBOARD
# This script will display detailed information about what's happening

# Record script directory
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
echo "📂 Script directory: $SCRIPT_DIR"

# Clear terminal
clear

# Print header
echo "==============================================================="
echo "🔍 VERBOSE DEBUG LAUNCHER FOR TRADING DASHBOARD"
echo "==============================================================="
echo "This script will show detailed information to diagnose problems"

# List files in the current directory
echo -e "\n📄 Files in the current directory:"
ls -la

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo -e "\n✅ Virtual environment found"
    # Activate virtual environment
    echo "🔄 Activating virtual environment..."
    source venv/bin/activate
    echo "🐍 Python version: $(python --version)"
else
    echo -e "\n❌ ERROR: Virtual environment 'venv' not found!"
    echo "Creating a new virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
fi

# Check application directory
DASHBOARD_DIR="$SCRIPT_DIR/trading_bot/dashboard"
if [ -d "$DASHBOARD_DIR" ]; then
    echo -e "\n✅ Dashboard directory found at: $DASHBOARD_DIR"
    echo "📄 Files in dashboard directory:"
    ls -la "$DASHBOARD_DIR"
else
    echo -e "\n❌ ERROR: Dashboard directory not found at: $DASHBOARD_DIR"
    exit 1
fi

# Check app.py 
APP_PATH="$DASHBOARD_DIR/app.py"
if [ -f "$APP_PATH" ]; then
    echo -e "\n✅ Found app.py at: $APP_PATH"
    echo "📄 First 10 lines of app.py:"
    head -n 10 "$APP_PATH"
else
    echo -e "\n❌ ERROR: app.py not found at: $APP_PATH"
    exit 1
fi

# Install needed packages
echo -e "\n📦 Installing required packages..."
python -m pip install --upgrade pip
echo "Installing Streamlit..."
python -m pip install streamlit
echo "Installing other potential requirements..."
python -m pip install flask flask-socketio flask-cors pandas numpy

# Try to determine app type
echo -e "\n🔍 Detecting app type..."
APP_TYPE=$(python -c "
import sys, os
sys.path.insert(0, '$DASHBOARD_DIR')
try:
    import app
    if hasattr(app, 'socketio'):
        print('flask')
    elif hasattr(app, 'st'):
        print('streamlit')
    else:
        print('unknown')
except Exception as e:
    print(f'error: {str(e)}')
")

echo "🔍 Detected app type: $APP_TYPE"

# Run based on app type
echo -e "\n🚀 Attempting to launch dashboard..."

if [[ "$APP_TYPE" == *"streamlit"* ]]; then
    echo "📊 Running as Streamlit app on port 8080"
    echo "Command: streamlit run $APP_PATH --server.port 8080 --server.address 0.0.0.0"
    streamlit run "$APP_PATH" --server.port 8080 --server.address 0.0.0.0
elif [[ "$APP_TYPE" == *"flask"* ]]; then
    echo "🌐 Running as Flask app on port 8080"
    echo "Command: python -c \"
import sys, os
sys.path.insert(0, '$DASHBOARD_DIR')
import app
app.socketio.run(app.app, debug=True, host='0.0.0.0', port=8080)
\""
    python -c "
import sys, os
sys.path.insert(0, '$DASHBOARD_DIR')
import app
app.socketio.run(app.app, debug=True, host='0.0.0.0', port=8080)
"
else
    echo "⚠️ Could not determine app type. Trying direct execution..."
    echo "Command: python $APP_PATH"
    python "$APP_PATH"
fi

# Keep terminal window open to see errors
echo -e "\n==============================================================="
echo "Dashboard server has stopped or encountered an error."
echo "Check the output above for error messages."
echo "==============================================================="
read -p "Press Enter to close this window..." key 