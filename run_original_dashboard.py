#!/usr/bin/env python3
"""
Run Original Dashboard
This script properly sets up the Python path and runs the original dashboard.
"""

import os
import sys
import importlib.util
from pathlib import Path

# Get the absolute path to the project root directory
project_dir = os.path.dirname(os.path.abspath(__file__))

# Add the project root to Python path for imports
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

# Try to import and fix any common import errors
try:
    # For any modules that might have import issues
    from trading_bot.portfolio_state import PortfolioStateManager
except ImportError as e:
    print(f"Warning: {e}")
    print("Installing missing dependencies...")
    import subprocess
    subprocess.call([sys.executable, "-m", "pip", "install", "flask", "plotly", "pandas", "numpy"])

# Try to run the app
try:
    print("\n🚀 Starting Original Dashboard...\n")
    print("If the dashboard doesn't start, try the following:")
    print("1. Make sure you have all dependencies: pip install -r requirements.txt")
    print("2. Make sure trading_bot is installed as a package: pip install -e .\n")
    
    # Import the app.py from the main directory
    import app
    
    # Run the app on port 8080
    app.socketio.run(app.app, debug=True, host='0.0.0.0', port=8080)
    
except Exception as e:
    print(f"\nError starting dashboard: {e}")
    
    # Try alternative approaches
    print("\nTrying alternative approach...")
    try:
        os.chdir(project_dir)
        os.environ["PYTHONPATH"] = project_dir
        
        # Try running the dashboard directly
        from trading_bot.dashboard.app import app, socketio
        socketio.run(app, debug=True, host='0.0.0.0', port=8080)
    except Exception as e2:
        print(f"\nAlternative approach also failed: {e2}")
        print("\nPlease run the following command manually:")
        print("PYTHONPATH=/Users/bendickinson/Desktop/Trading python -m trading_bot.dashboard.run_dashboard") 