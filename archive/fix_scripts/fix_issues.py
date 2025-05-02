#!/usr/bin/env python3
"""
Fix script for Trading application issues
Resolves API rate limiting, dependencies, and port conflicts
"""

import os
import json
import time
import subprocess
import logging
import socket
from pathlib import Path
import sys
import platform
from typing import Dict, List, Optional, Any, Tuple

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ApiRateLimitFixer:
    """
    Manages API rate limiting and cycling through available APIs
    to prevent hitting limits for any single provider.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the API rate limit fixer.
        
        Args:
            config_path: Path to the API configuration file
        """
        self.config_path = config_path or 'api_config.json'
        self.api_data = self._load_config()
        self._update_usage_stats()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load API configuration from file or create default"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON in {self.config_path}, creating new config")
        
        # Default configuration
        return {
            'apis': {
                'nytimes': {
                    'daily_limit': 1000, 
                    'usage': 0, 
                    'cooldown_minutes': 5,
                    'priority': 1,
                    'last_used': 0
                },
                'finnhub': {
                    'daily_limit': 500, 
                    'usage': 0, 
                    'cooldown_minutes': 5,
                    'priority': 2,
                    'last_used': 0
                },
                'marketaux': {
                    'daily_limit': 100, 
                    'usage': 0, 
                    'cooldown_minutes': 300,  # 5 minutes
                    'priority': 3,
                    'last_used': 0
                },
                'newsdata': {
                    'daily_limit': 200, 
                    'usage': 0, 
                    'cooldown_minutes': 3600,  # 1 hour
                    'priority': 4,
                    'last_used': 0
                },
                'gnews': {
                    'daily_limit': 100, 
                    'usage': 0, 
                    'cooldown_minutes': 900,  # 15 minutes
                    'priority': 5,
                    'last_used': 0
                },
                'mediastack': {
                    'daily_limit': 500, 
                    'usage': 0, 
                    'cooldown_minutes': 60,  # 1 minute
                    'priority': 6,
                    'last_used': 0
                },
                'currents': {
                    'daily_limit': 200, 
                    'usage': 0, 
                    'cooldown_minutes': 120,  # 2 minutes
                    'priority': 7,
                    'last_used': 0
                }
            },
            'date': time.strftime('%Y-%m-%d')
        }
    
    def _update_usage_stats(self) -> None:
        """Reset usage counters if it's a new day"""
        current_date = time.strftime('%Y-%m-%d')
        if self.api_data.get('date') != current_date:
            logger.info("New day detected, resetting API usage counters")
            for api in self.api_data['apis']:
                self.api_data['apis'][api]['usage'] = 0
            self.api_data['date'] = current_date
            self._save_config()
    
    def _save_config(self) -> None:
        """Save current API configuration to file"""
        with open(self.config_path, 'w') as f:
            json.dump(self.api_data, f, indent=2)
    
    def get_next_api(self, api_type: str = 'news') -> Optional[str]:
        """
        Get the next available API based on rate limits and cooldown
        
        Args:
            api_type: Type of API to get (news, market, etc.)
            
        Returns:
            Name of the next available API or None if all are rate limited
        """
        available_apis = []
        current_time = time.time()
        
        for api_name, api_info in self.api_data['apis'].items():
            # Skip if this API doesn't match the requested type
            # In a real implementation, we would filter by API type
            
            # Check if API is under limit
            usage_percent = api_info['usage'] / api_info['daily_limit']
            
            # Check if cooldown period has passed
            last_used = api_info.get('last_used', 0)
            time_since_last_call = current_time - last_used
            cooldown_passed = time_since_last_call > (api_info['cooldown_minutes'] * 60)
            
            if usage_percent < 0.95 and cooldown_passed:
                # API is available
                available_apis.append((
                    api_name, 
                    api_info['priority'],
                    usage_percent
                ))
        
        if not available_apis:
            logger.warning("All APIs are currently rate limited")
            return None
        
        # Sort by priority first, then by usage percentage
        available_apis.sort(key=lambda x: (x[1], x[2]))
        selected_api = available_apis[0][0]
        
        logger.info(f"Selected API: {selected_api}")
        return selected_api
    
    def log_api_call(self, api_name: str) -> None:
        """
        Log an API call and update usage stats
        
        Args:
            api_name: Name of the API that was called
        """
        if api_name not in self.api_data['apis']:
            logger.warning(f"Unknown API: {api_name}")
            return
        
        self.api_data['apis'][api_name]['usage'] += 1
        self.api_data['apis'][api_name]['last_used'] = time.time()
        self._save_config()
        
        logger.info(f"Logged call to {api_name}. Total usage today: {self.api_data['apis'][api_name]['usage']}")
    
    def get_usage_stats(self) -> Dict[str, int]:
        """Get current API usage statistics"""
        return {
            api_name: api_info['usage'] 
            for api_name, api_info in self.api_data['apis'].items()
        }

class DependencyFixer:
    """Fixes Python dependencies and environment issues"""
    
    def __init__(self):
        self.python_exec = sys.executable
        self.os_name = platform.system()
        
    def fix_pandas_issue(self) -> bool:
        """
        Fix pandas installation issue by installing a compatible version
        
        Returns:
            True if successful, False otherwise
        """
        logger.info("Fixing pandas installation issue...")
        
        # For Python 3.13 compatibility
        if sys.version_info.major == 3 and sys.version_info.minor >= 13:
            logger.info(f"Detected Python 3.13+: {sys.version}")
            # Using an older version that's compatible with Python 3.13
            return self._install_package("pandas==2.0.0") 
        else:
            # For other Python versions, try the latest pre-built version
            return self._install_package("pandas")
    
    def _install_package(self, package_spec: str) -> bool:
        """
        Install a Python package
        
        Args:
            package_spec: Package specification (e.g. "pandas==2.0.0")
            
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Installing {package_spec}...")
        try:
            subprocess.check_call([self.python_exec, "-m", "pip", "install", package_spec])
            logger.info(f"Successfully installed {package_spec}")
            return True
        except subprocess.CalledProcessError:
            logger.error(f"Failed to install {package_spec}")
            return False
    
    def install_requirements(self, requirements_file: str = "requirements.txt") -> bool:
        """
        Install packages from requirements file
        
        Args:
            requirements_file: Path to requirements.txt
            
        Returns:
            True if successful, False otherwise
        """
        if not os.path.exists(requirements_file):
            logger.error(f"Requirements file {requirements_file} not found")
            return False
        
        try:
            logger.info(f"Installing dependencies from {requirements_file}...")
            subprocess.check_call([self.python_exec, "-m", "pip", "install", "-r", requirements_file])
            logger.info("Successfully installed dependencies")
            return True
        except subprocess.CalledProcessError:
            logger.error(f"Failed to install dependencies from {requirements_file}")
            return False

class PortManager:
    """Manages port allocation for web servers"""
    
    @staticmethod
    def find_available_port(start_port: int = 8000, max_attempts: int = 100) -> int:
        """
        Find an available port
        
        Args:
            start_port: Port to start searching from
            max_attempts: Maximum number of ports to check
            
        Returns:
            Available port number
            
        Raises:
            RuntimeError: If no available port is found
        """
        for port in range(start_port, start_port + max_attempts):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.bind(('localhost', port))
                sock.close()
                logger.info(f"Found available port: {port}")
                return port
            except OSError:
                continue
        
        raise RuntimeError(f"Could not find an available port after {max_attempts} attempts")
    
    @staticmethod
    def update_port_in_file(file_path: str, new_port: int) -> bool:
        """
        Update port number in a file
        
        Args:
            file_path: Path to the file
            new_port: New port number
            
        Returns:
            True if successful, False otherwise
        """
        if not os.path.exists(file_path):
            logger.error(f"File {file_path} not found")
            return False
        
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Update port in Flask app
            if 'app.run(host=' in content:
                content = content.replace(
                    "app.run(host='0.0.0.0', port=5000", 
                    f"app.run(host='0.0.0.0', port={new_port}"
                )
                
                # Also update debug statement if it exists
                content = content.replace(
                    "app.run(debug=True", 
                    f"app.run(debug=True, port={new_port}"
                )
            
            with open(file_path, 'w') as f:
                f.write(content)
            
            logger.info(f"Updated port in {file_path} to {new_port}")
            return True
        except Exception as e:
            logger.error(f"Failed to update port in {file_path}: {e}")
            return False

def create_momentum_strategy_file() -> bool:
    """
    Create the momentum strategy file if it doesn't exist
    
    Returns:
        True if successful, False otherwise
    """
    strategy_dir = Path("trading_bot/strategies")
    file_path = strategy_dir / "momentum_strategy.py"
    
    # Ensure the directory exists
    strategy_dir.mkdir(parents=True, exist_ok=True)
    
    if file_path.exists():
        logger.info(f"{file_path} already exists")
        return True
    
    try:
        logger.info(f"Creating {file_path}...")
        with open(file_path, 'w') as f:
            f.write('''import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List, Tuple
import logging

logger = logging.getLogger(__name__)

class MomentumStrategy:
    """
    Momentum trading strategy implementation that identifies and trades based on
    price momentum and trend strength.
    """
    
    def __init__(self, lookback_period: int = 14, overbought: int = 70, oversold: int = 30):
        """
        Initialize the momentum strategy with configurable parameters.
        
        Args:
            lookback_period: Period for calculating momentum indicators
            overbought: RSI threshold for overbought condition
            oversold: RSI threshold for oversold condition
        """
        self.name = "Momentum"
        self.lookback_period = lookback_period
        self.overbought = overbought
        self.oversold = oversold
        self.description = "Trades based on price momentum and trend strength"
        
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Generate trade signals based on momentum indicators.
        
        Args:
            data: DataFrame with OHLCV price data
            
        Returns:
            DataFrame with added momentum indicators and trade signals
        """
        if len(data) < self.lookback_period:
            return pd.DataFrame()
        
        # Calculate price momentum (close price change over lookback period)
        data = data.copy()
        data['momentum'] = data['close'].pct_change(self.lookback_period)
        
        # Calculate Rate of Change (ROC)
        data['roc'] = (data['close'] / data['close'].shift(self.lookback_period) - 1) * 100
        
        # Calculate RSI
        delta = data['close'].diff()
        gain = delta.where(delta > 0, 0).rolling(window=self.lookback_period).mean()
        loss = -delta.where(delta < 0, 0).rolling(window=self.lookback_period).mean()
        
        rs = gain / loss
        data['rsi'] = 100 - (100 / (1 + rs))
        
        # Generate signals
        data['signal'] = 0  # 0 = no signal, 1 = buy, -1 = sell
        
        # Buy when momentum is positive and RSI was oversold but is increasing
        data.loc[(data['momentum'] > 0) & 
                 (data['rsi'] > self.oversold) & 
                 (data['rsi'].shift(1) <= self.oversold), 'signal'] = 1
        
        # Sell when momentum turns negative or RSI is overbought
        data.loc[(data['momentum'] < 0) | 
                 (data['rsi'] >= self.overbought), 'signal'] = -1
        
        return data
    
    def get_parameters(self) -> Dict[str, Any]:
        """Return strategy parameters"""
        return {
            "lookback_period": self.lookback_period,
            "overbought": self.overbought,
            "oversold": self.oversold
        }
    
    def set_parameters(self, params: Dict[str, Any]) -> None:
        """Set strategy parameters"""
        if 'lookback_period' in params:
            self.lookback_period = params['lookback_period']
        if 'overbought' in params:
            self.overbought = params['overbought']
        if 'oversold' in params:
            self.oversold = params['oversold']
''')
        logger.info(f"Successfully created {file_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to create momentum strategy file: {e}")
        return False

def modify_app_import_for_momentum_strategy() -> bool:
    """
    Update the app.py file to import the momentum strategy
    
    Returns:
        True if successful, False otherwise
    """
    app_path = "app.py"
    
    if not os.path.exists(app_path):
        logger.error(f"App file {app_path} not found")
        return False
    
    try:
        with open(app_path, 'r') as f:
            content = f.read()
        
        # Check if the import already exists
        if "from trading_bot.strategies.momentum_strategy import MomentumStrategy" in content:
            logger.info("MomentumStrategy import already exists in app.py")
            return True
        
        # Find the imports section and add our import
        import_lines = content.split('\n')
        import_section_end = 0
        
        for i, line in enumerate(import_lines):
            if line.startswith('import') or line.startswith('from'):
                import_section_end = i
        
        import_lines.insert(import_section_end + 1, 
                            "from trading_bot.strategies.momentum_strategy import MomentumStrategy")
        
        # Write the updated content
        with open(app_path, 'w') as f:
            f.write('\n'.join(import_lines))
        
        logger.info("Successfully added MomentumStrategy import to app.py")
        return True
    except Exception as e:
        logger.error(f"Failed to update app.py: {e}")
        return False

def fix_ai_backtest_endpoint() -> bool:
    """
    Fix the AI backtest endpoint to use a different port
    
    Returns:
        True if successful, False otherwise
    """
    file_path = "ai_backtest_endpoint.py"
    
    if not os.path.exists(file_path):
        logger.error(f"File {file_path} not found")
        return False
    
    try:
        # Find an available port
        port = PortManager.find_available_port(8000)
        
        # Update the file with the new port
        return PortManager.update_port_in_file(file_path, port)
    except Exception as e:
        logger.error(f"Failed to fix AI backtest endpoint: {e}")
        return False

def create_strategy_factory_init() -> bool:
    """
    Create __init__.py file in the strategies directory
    
    Returns:
        True if successful, False otherwise
    """
    strategy_dir = Path("trading_bot/strategies")
    init_path = strategy_dir / "__init__.py"
    
    # Ensure the directory exists
    strategy_dir.mkdir(parents=True, exist_ok=True)
    
    if init_path.exists():
        logger.info(f"{init_path} already exists")
        return True
    
    try:
        logger.info(f"Creating {init_path}...")
        with open(init_path, 'w') as f:
            f.write('''"""
Trading bot strategy implementations
"""

__all__ = ["momentum_strategy"]
''')
        logger.info(f"Successfully created {init_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to create strategies __init__.py: {e}")
        return False

def main():
    """Main entry point for fixing issues"""
    logger.info("Starting fix script...")
    
    # Fix API rate limiting
    api_fixer = ApiRateLimitFixer()
    logger.info(f"Current API usage: {api_fixer.get_usage_stats()}")
    
    # Fix momentum strategy
    if create_momentum_strategy_file() and create_strategy_factory_init():
        logger.info("Successfully created momentum strategy files")
        
        # Update app.py to import the momentum strategy
        if modify_app_import_for_momentum_strategy():
            logger.info("Successfully updated app.py for momentum strategy")
    
    # Fix AI backtest endpoint port
    if fix_ai_backtest_endpoint():
        logger.info("Successfully fixed AI backtest endpoint port")
    
    # Fix dependencies
    dep_fixer = DependencyFixer()
    if dep_fixer.fix_pandas_issue():
        logger.info("Successfully fixed pandas installation")
    
    logger.info("Fix script completed")

if __name__ == "__main__":
    main() 