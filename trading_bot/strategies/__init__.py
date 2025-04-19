"""
Trading Strategies Package

This package contains various trading strategies organized by asset class:
- Stock strategies (swing, momentum, breakout, mean reversion)
- Options strategies (income, spreads, volatility)
- Crypto strategies
- Forex strategies
"""

# Import from asset-specific packages
from trading_bot.strategies.stocks import *
from trading_bot.strategies.options import *
from trading_bot.strategies.crypto import *
from trading_bot.strategies.forex import *

# Import from timeframe-based packages (legacy)
from trading_bot.strategies.timeframe import *

# Import ML and advanced strategies
from trading_bot.strategies.ml_strategy import MLStrategy

# Import base classes and common utilities
from trading_bot.strategies.strategy_template import (
    StrategyTemplate, 
    StrategyOptimizable,
    Signal, 
    SignalType,
    TimeFrame,
    MarketRegime
)

# Import feature engineering directly for easier access
from trading_bot.utils.feature_engineering import FeatureEngineering

# Import base strategy classes
from trading_bot.strategies.base import (
    StockBaseStrategy,
    OptionsBaseStrategy,
    CryptoBaseStrategy,
    ForexBaseStrategy
)

__all__ = [
    # Base classes
    'StrategyTemplate',
    'StrategyOptimizable',
    'Signal',
    'SignalType',
    'TimeFrame',
    'MarketRegime',
    
    # Asset-specific base classes
    'StockBaseStrategy',
    'OptionsBaseStrategy',
    'CryptoBaseStrategy',
    'ForexBaseStrategy',
    
    # Advanced strategies
    'MLStrategy',
    
    # Feature engineering
    'FeatureEngineering',
    
    # Import all strategies from subpackages
    # These will be populated from the imports above
] 