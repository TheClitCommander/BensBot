"""
Options Strategies Module

This module provides option-specific trading strategies organized by strategy type.
"""

from trading_bot.strategies.options.income import CoveredCallStrategy, CashSecuredPutStrategy, MarriedPutStrategy
from trading_bot.strategies.options.spreads import (
    BullCallSpreadStrategy, BullPutSpreadStrategy, BearPutSpreadStrategy,
    IronCondorStrategy, ButterflySpread, CalendarSpread,
    CollarStrategy, RatioSpread, StrangleStrategy
)

__all__ = [
    # Income strategies
    'CoveredCallStrategy',
    'CashSecuredPutStrategy',
    'MarriedPutStrategy',
    
    # Spread strategies
    'BullCallSpreadStrategy',
    'BullPutSpreadStrategy',
    'BearPutSpreadStrategy',
    'IronCondorStrategy',
    'ButterflySpread', 
    'CalendarSpread',
    'CollarStrategy',
    'RatioSpread',
    'StrangleStrategy',
] 