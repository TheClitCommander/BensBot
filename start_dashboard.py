#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Dashboard Starter Script

This script ensures the correct environment setup and launches the dashboard
"""

import os
import sys
import subprocess
import signal
import time
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add the project root directory to Python path
sys.path.insert(0, os.path.abspath(os.getcwd()))

# Set the port to use
PORT = 5555

def main():
    """Main function to start the dashboard with proper environment setup"""
    try:
        # Print header
        print("=" * 60)
        logger.info("Starting Trading Bot Dashboard...")
        print("=" * 60)
        
        # Add the project root to Python path
        project_root = Path(os.path.dirname(os.path.abspath(__file__)))
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))
        
        # Import server components after path is correctly set
        from trading_bot.dashboard.dashboard_server import app, socketio
        
        # Use a different port to avoid conflicts
        port = 5555
        
        print(f"Dashboard will be available at: http://localhost:{port}")
        print("Press Ctrl+C to stop the server")
        print("=" * 60)
        
        # Run the dashboard app
        socketio.run(app, host='0.0.0.0', port=port, debug=True)
        
    except ImportError as e:
        logger.error(f"Import error: {e}")
        print("\nERROR: Missing required module.")
        print(f"Please install it with: pip install {str(e).split(' ')[-1]}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error starting dashboard: {e}")
        print("\nERROR: Failed to start dashboard.")
        print(f"Details: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 