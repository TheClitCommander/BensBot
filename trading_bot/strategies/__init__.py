"""
Trading Strategies Package

This package contains various trading strategies organized by category:
- Timeframe-based strategies (swing, day, position, etc.)
- Options income strategies (covered calls, cash-secured puts, etc.)
- Options spread strategies (butterflies, iron condors, etc.)
"""

# Import from category packages
from trading_bot.strategies.timeframe import *
from trading_bot.strategies.options_income import *
from trading_bot.strategies.options_spreads import *

# Import base classes and common utilities
from trading_bot.strategies.strategy_template import (
    StrategyTemplate, 
    StrategyOptimizable,
    Signal, 
    SignalType,
    TimeFrame,
    MarketRegime
)

__all__ = [
    # Base classes
    'StrategyTemplate',
    'StrategyOptimizable',
    'Signal',
    'SignalType',
    'TimeFrame',
    'MarketRegime',
    
    # Import all strategies from subpackages
    # These will be populated from the imports above
] 