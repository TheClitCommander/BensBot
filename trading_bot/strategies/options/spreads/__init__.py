"""
Options Spread Strategies Module

This module provides option spread strategies, focusing on vertical, horizontal,
diagonal, and other multi-leg option spreads.
"""

# Import classes once they are added
from trading_bot.strategies.options.spreads.bull_call_spread_strategy import BullCallSpreadStrategy
from trading_bot.strategies.options.spreads.bull_put_spread_strategy import BullPutSpreadStrategy
from trading_bot.strategies.options.spreads.bear_put_spread_strategy import BearPutSpreadStrategy
# from trading_bot.strategies.options.spreads.iron_condor_strategy import IronCondorStrategy
# from trading_bot.strategies.options.spreads.butterfly_spread import ButterflySpread
# from trading_bot.strategies.options.spreads.calendar_spread import CalendarSpread
# from trading_bot.strategies.options.spreads.collar_strategy import CollarStrategy
# from trading_bot.strategies.options.spreads.ratio_spread import RatioSpread
# from trading_bot.strategies.options.spreads.strangle_strategy import StrangleStrategy

__all__ = [
    'BullCallSpreadStrategy',
    'BullPutSpreadStrategy',
    'BearPutSpreadStrategy',
    # 'IronCondorStrategy',
    # 'ButterflySpread',
    # 'CalendarSpread',
    # 'CollarStrategy',
    # 'RatioSpread',
    # 'StrangleStrategy',
] 