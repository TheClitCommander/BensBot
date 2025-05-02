#!/usr/bin/env python3
"""
Direct Dashboard Runner

This script runs the dashboard directly without relying on package imports.
"""

import os
import sys
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main function to run the dashboard app directly"""
    try:
        logger.info("Starting Trading Bot Dashboard (Direct Mode)...")
        
        # Import app.py directly from the current directory
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import app
        
        # Get port from environment or use default
        port = int(os.environ.get('PORT', 8080))  # Changed from 5000 to 8080
        
        # Run the app
        app.socketio.run(app.app, debug=True, host='0.0.0.0', port=port)
        
    except Exception as e:
        logger.error(f"Error starting dashboard: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 