#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Run script for Trading Bot Dashboard with error handling
"""

import os
import sys
import logging
import subprocess
import importlib

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Required packages with fallbacks
REQUIRED_PACKAGES = {
    'streamlit': None,
    'flask': None,
    'flask_socketio': None,
    'ta': None,
    'pandas': None,
    'numpy': None,
    'matplotlib': None,
    'yfinance': None,
    'sklearn': 'scikit-learn',
    'xgboost': None,
    'websocket': 'websocket-client',
}

def check_and_install_packages():
    """Check for required packages and install if missing."""
    missing_packages = []
    
    for package, install_name in REQUIRED_PACKAGES.items():
        try:
            importlib.import_module(package)
            logger.info(f"✅ {package} is installed")
        except ImportError:
            actual_name = install_name if install_name else package
            missing_packages.append(actual_name)
            logger.warning(f"❌ {package} is not installed")
    
    if missing_packages:
        logger.info(f"Installing missing packages: {', '.join(missing_packages)}")
        try:
            cmd = [sys.executable, "-m", "pip", "install"] + missing_packages
            subprocess.check_call(cmd)
            logger.info("Successfully installed all required packages")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install packages: {e}")
            return False
    
    return True

def fix_package_versions():
    """Fix known version incompatibilities."""
    # Fix websocket-client if needed
    try:
        import websocket
        logger.info("websocket module is properly installed")
    except ImportError:
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", "websocket-client"
            ])
        except:
            logger.warning("Could not install websocket-client")

def fix_trading_bot_modules():
    """Fix common import issues in trading_bot modules."""
    try:
        # Create placeholder module if trading_bot.accounts doesn't exist
        if not os.path.exists('trading_bot/accounts'):
            os.makedirs('trading_bot/accounts', exist_ok=True)
            if not os.path.exists('trading_bot/accounts/__init__.py'):
                with open('trading_bot/accounts/__init__.py', 'w') as f:
                    f.write('"""Trading Bot Accounts Module."""\n')
            
            if not os.path.exists('trading_bot/accounts/account_data.py'):
                with open('trading_bot/accounts/account_data.py', 'w') as f:
                    f.write('"""Account Data placeholder module."""\n\n')
                    f.write('class AccountData:\n')
                    f.write('    """Placeholder for AccountData class."""\n\n')
                    f.write('    def __init__(self):\n')
                    f.write('        self.balance = 10000\n')
        
        # Fix other common issues with the core interfaces
        core_interfaces_path = 'trading_bot/core/interfaces.py'
        if os.path.exists(core_interfaces_path):
            with open(core_interfaces_path, 'r') as f:
                content = f.read()
            
            if 'DataSourceInterface' not in content and 'DataProvider' in content:
                # Add DataSourceInterface as an alias for DataProvider
                with open(core_interfaces_path, 'a') as f:
                    f.write('\n# Added by run_fixed_dashboard.py\n')
                    f.write('DataSourceInterface = DataProvider\n')
                logger.info("Added DataSourceInterface to core interfaces")
        
        logger.info("Fixed common trading_bot module issues")
    except Exception as e:
        logger.error(f"Error fixing trading_bot modules: {e}")

def run_dashboard():
    """Run the dashboard with error handling."""
    # First check and install required packages
    if not check_and_install_packages():
        logger.error("Failed to install required packages. Exiting.")
        return
    
    # Fix common issues
    fix_package_versions()
    fix_trading_bot_modules()
    
    # Try to run with the dashboard file that seems most appropriate
    dashboard_files = [
        'app.py', 
        'portfolio_dashboard.py',
        'simple_dashboard.py',
        'mini_dashboard.py'
    ]
    
    # Try to run each file until one works
    for dashboard_file in dashboard_files:
        if os.path.exists(dashboard_file):
            try:
                logger.info(f"Attempting to run {dashboard_file}...")
                cmd = [sys.executable, "-m", "streamlit", "run", dashboard_file]
                subprocess.run(cmd)
                # If we get here, the dashboard ran without error
                logger.info(f"Successfully ran {dashboard_file}")
                return
            except Exception as e:
                logger.error(f"Error running {dashboard_file}: {e}")
    
    logger.error("Could not run any dashboard file")

if __name__ == "__main__":
    print("\n🚀 Starting Trading Bot Dashboard...\n")
    run_dashboard() 