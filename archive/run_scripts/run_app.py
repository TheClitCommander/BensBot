#!/usr/bin/env python3
"""
Helper script to run the trading bot app with module fallbacks and error handling.
"""

import sys
import os
import subprocess
import logging
import importlib

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("app_runner")

def ensure_module(module_name):
    """Ensure a module is installed, install if missing."""
    try:
        importlib.import_module(module_name)
        return True
    except ImportError:
        logger.warning(f"Module {module_name} not found. Attempting to install...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", module_name])
            logger.info(f"Successfully installed {module_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to install {module_name}: {e}")
            return False

def fix_import_error(error_message):
    """Try to fix common import errors."""
    if "No module named 'flask'" in error_message:
        ensure_module("flask")
    elif "No module named 'pandas'" in error_message:
        ensure_module("pandas")
    elif "No module named 'yfinance'" in error_message:
        ensure_module("yfinance")
    elif "No module named 'streamlit'" in error_message:
        ensure_module("streamlit")
    elif "No module named 'plotly'" in error_message:
        ensure_module("plotly")
    elif "No module named 'matplotlib'" in error_message:
        ensure_module("matplotlib")
    elif "No module named 'sklearn'" in error_message:
        ensure_module("scikit-learn")
    else:
        logger.error(f"Unknown import error: {error_message}")
        return False
    return True

def main():
    """Main function to run the streamlit app with error handling."""
    # Ensure the project root is in the Python path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
        
    # Check for missing essential modules
    essential_modules = ["streamlit", "pandas", "numpy", "matplotlib", "plotly"]
    missing_modules = []
    
    for module in essential_modules:
        if not ensure_module(module):
            missing_modules.append(module)
    
    if missing_modules:
        logger.error(f"Unable to run app due to missing modules: {', '.join(missing_modules)}")
        logger.error("Please install them manually using pip install <module_name>")
        return 1
        
    try:
        # Try to run the streamlit app
        logger.info("Starting streamlit app...")
        subprocess.check_call([sys.executable, "-m", "streamlit", "run", "app.py"])
        return 0
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running streamlit app: {e}")
        return 1
    except Exception as e:
        # Check if it's an import error
        error_message = str(e)
        if "No module named" in error_message:
            if fix_import_error(error_message):
                logger.info("Fixed import error. Retrying...")
                # Retry running the app
                return main()
        
        logger.error(f"Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 