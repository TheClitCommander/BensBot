#!/usr/bin/env python3
"""
Streamlit Dashboard Runner

This script runs the dashboard using Streamlit.
"""

import os
import sys
import logging
import subprocess
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main function to run the dashboard app with Streamlit"""
    try:
        logger.info("Starting Trading Bot Dashboard with Streamlit...")
        
        # Get dashboard directory
        dashboard_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'trading_bot', 'dashboard')
        app_path = os.path.join(dashboard_dir, 'app.py')
        
        if not os.path.exists(app_path):
            logger.error(f"Dashboard app not found at: {app_path}")
            return
        
        # Streamlit needs to be installed
        try:
            import streamlit
            logger.info("Streamlit is installed")
        except ImportError:
            logger.info("Installing Streamlit...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "streamlit"])
            logger.info("Streamlit installed successfully")
        
        # Build the Streamlit command
        port = 8080
        cmd = [
            sys.executable,
            "-m", "streamlit", "run",
            app_path,
            "--server.port", str(port),
            "--server.address", "0.0.0.0"
        ]
        
        # Print information
        logger.info(f"Running command: {' '.join(cmd)}")
        logger.info(f"Dashboard will be available at: http://localhost:{port}")
        
        # Run Streamlit
        subprocess.run(cmd)
        
    except Exception as e:
        logger.error(f"Error starting dashboard: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 