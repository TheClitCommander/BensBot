#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Trading Bot Dashboard Runner

This script launches the trading bot dashboard application.
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

# Add the parent directory to sys.path to support imports
current_dir = Path(os.path.dirname(os.path.abspath(__file__)))
parent_dir = current_dir.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

def main():
    """Main function to run the dashboard app"""
    try:
        logger.info("Starting Trading Bot Dashboard...")
        
        # Import the app from the dashboard module
        from trading_bot.dashboard.app import app, socketio

        # Get port from environment or use default
        port = int(os.environ.get('PORT', 8080))
        
        # Run the app
        socketio.run(app, debug=True, host='0.0.0.0', port=port)
        
    except Exception as e:
        logger.error(f"Error starting dashboard: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 