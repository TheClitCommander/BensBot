#!/usr/bin/env python3
"""
Trading Strategy Dashboard Launcher

This script launches the Streamlit dashboard for the trading strategy system.
It handles setting environment variables and initializing connections needed for the dashboard.
"""

import os
import sys
import subprocess
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("dashboard_launcher")

def check_requirements():
    """Check if all required packages are installed."""
    required = ["streamlit", "pandas", "numpy", "plotly"]
    missing = []
    
    for package in required:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    if missing:
        logger.error(f"Missing required packages: {', '.join(missing)}")
        logger.info("Installing missing packages...")
        
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", *missing
            ])
            logger.info("Successfully installed missing packages.")
        except subprocess.CalledProcessError:
            logger.error("Failed to install packages. Please install them manually.")
            sys.exit(1)

def load_environment_variables():
    """Load environment variables from .env file if present."""
    if os.path.exists(".env"):
        logger.info("Loading environment variables from .env file")
        load_dotenv()
    else:
        logger.warning(".env file not found. Using system environment variables.")
    
    # Check for critical environment variables
    critical_vars = []
    for var in critical_vars:
        if not os.environ.get(var):
            logger.warning(f"Environment variable {var} not set")

def launch_dashboard():
    """Launch the Streamlit dashboard."""
    logger.info("Launching Trading Strategy Dashboard...")
    
    try:
        # Use Streamlit to run the app
        subprocess.run([
            "streamlit", "run", "app.py",
            "--server.port", "8501",
            "--browser.serverAddress", "localhost",
            "--theme.primaryColor", "#1E88E5",
            "--theme.backgroundColor", "#FFFFFF",
            "--theme.secondaryBackgroundColor", "#F8F9FA",
            "--theme.textColor", "#424242"
        ], check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to launch dashboard: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Dashboard stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("=" * 80)
    print("Trading Strategy Dashboard - Launcher")
    print("=" * 80)
    
    # Check requirements
    check_requirements()
    
    # Load environment variables
    load_environment_variables()
    
    # Launch dashboard
    launch_dashboard() 