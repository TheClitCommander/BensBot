"""
Trading Strategies Module

This module contains the implementations of various trading strategies.
"""

from trading_bot.strategies.trend_following import TrendFollowingStrategy
from trading_bot.strategies.momentum import MomentumStrategy
from trading_bot.strategies.mean_reversion import MeanReversionStrategy
from trading_bot.strategies.breakout_swing import BreakoutSwingStrategy
from trading_bot.strategies.volatility_breakout import VolatilityBreakoutStrategy
from trading_bot.strategies.option_spreads import OptionSpreadsStrategy

__all__ = [
    'TrendFollowingStrategy',
    'MomentumStrategy',
    'MeanReversionStrategy',
    'BreakoutSwingStrategy',
    'VolatilityBreakoutStrategy',
    'OptionSpreadsStrategy'
] 