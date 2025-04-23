#!/usr/bin/env python3
"""
Simplified Runner for Trading Dashboard
This script handles common setup issues and launches the dashboard properly.
"""

import os
import sys
import subprocess
import logging
import time
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def install_requirements():
    """Install required packages if they're missing"""
    try:
        import importlib
        
        # Check for crucial packages
        missing_packages = []
        packages_to_check = ['streamlit', 'plotly', 'pandas', 'numpy', 'requests']
        
        for package in packages_to_check:
            try:
                importlib.import_module(package)
                logger.info(f"✓ {package} is installed")
            except ImportError:
                missing_packages.append(package)
                logger.warning(f"✗ {package} is missing")
        
        # Install missing packages
        if missing_packages:
            logger.info(f"Installing missing packages: {', '.join(missing_packages)}")
            subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing_packages)
            logger.info("Package installation completed")
        
        # Check for requirements.txt and install if present
        if Path("requirements.txt").exists():
            logger.info("Installing packages from requirements.txt")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
            logger.info("Requirements installation completed")
        
        return True
    except Exception as e:
        logger.error(f"Error installing requirements: {e}")
        return False

def setup_environment():
    """Set up environment variables for proper module imports"""
    # Get project root directory (parent of the directory containing this script)
    script_path = os.path.abspath(__file__)
    script_dir = os.path.dirname(script_path)
    project_root = os.path.dirname(script_dir) if "dashboard" in script_dir else os.path.dirname(os.path.abspath("."))
    
    # Add project root to Python path
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
        os.environ["PYTHONPATH"] = project_root
        logger.info(f"Added {project_root} to Python path")
    
    # Check if we're in a virtual environment
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        logger.warning("Not running in a virtual environment. It's recommended to use a virtual environment.")
    
    return project_root

def run_streamlit():
    """Run the dashboard using Streamlit"""
    try:
        # Check for app.py in current directory or project root
        project_root = setup_environment()
        app_path = os.path.join(project_root, "app.py")
        
        if not os.path.exists(app_path):
            logger.error(f"Dashboard app not found at {app_path}")
            return False
        
        # Print nice banner
        print("\n" + "=" * 60)
        print("🚀 Starting Trading Dashboard using Streamlit")
        print("=" * 60)
        print("If your browser doesn't open automatically, navigate to the URL below.")
        print("=" * 60 + "\n")
        
        # Run Streamlit
        streamlit_cmd = [sys.executable, "-m", "streamlit", "run", app_path]
        process = subprocess.Popen(streamlit_cmd)
        
        # Wait for process to end
        process.wait()
        return True
    
    except Exception as e:
        logger.error(f"Error running Streamlit: {e}")
        return False

def check_port_availability(port=8080):
    """Check if the specified port is available"""
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) != 0

def main():
    """Main entry point for running the dashboard"""
    try:
        logger.info("Starting Trading Dashboard setup...")
        
        # First, make sure required packages are installed
        if not install_requirements():
            logger.error("Failed to install required packages. Please check your Python environment.")
            sys.exit(1)
        
        # Set up environment
        setup_environment()
        
        # Check if a specific port is required
        port = 8501  # Default Streamlit port
        if not check_port_availability(port):
            logger.warning(f"Port {port} is already in use. Streamlit will try to use an alternative port.")
        
        # Run the dashboard using Streamlit
        if not run_streamlit():
            logger.error("Failed to start the dashboard. See log for details.")
            sys.exit(1)
        
    except KeyboardInterrupt:
        logger.info("Dashboard stopped by user")
    except Exception as e:
        logger.error(f"Error starting dashboard: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 