#!/usr/bin/env python3
"""
Simple script to run the trading bot API server with correct path setup.
This avoids Python package path issues when running the API directly.
"""
import os
import sys
import subprocess

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

try:
    # First check if we have the required packages
    try:
        import fastapi
        import uvicorn
    except ImportError:
        print("Installing required packages...")
        subprocess.run(["pip3", "install", "--user", "fastapi", "uvicorn"], check=True)
    
    print("Starting API server...")
    
    # Change to the project root
    os.chdir(project_root)
    
    # Import and run the app directly
    from trading_bot.api.app import app
    import uvicorn
    
    # Start the server
    uvicorn.run(app, host="0.0.0.0", port=5000)
    
except Exception as e:
    print(f"Error starting API server: {e}")
    print("Using fallback mock data mode. The dashboard will work but with simulated data.")
    sys.exit(1)
