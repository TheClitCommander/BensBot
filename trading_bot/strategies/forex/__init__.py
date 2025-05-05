#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Forex trading strategies.
"""

from . import momentum
from . import trend
from . import swing
from . import scalping
from . import breakout
from . import range

from .trend import ForexMomentumStrategy
from .trend import ForexTrendFollowingStrategy
from .breakout import ForexBreakoutStrategy
from .day_trading import ForexDayTradingStrategy
from .carry import ForexCarryTradeStrategy
from .swing import ForexSwingTradingStrategy
from .trend import ForexMomentumStrategy
from .trend import ForexGridTradingStrategy
from .trend import ForexRetracementStrategy
from .position import ForexPositionTradingStrategy
from .range import ForexRangeTradingStrategy
from .trend import ForexCounterTrendStrategy
from .scalping import ForexScalpingStrategy
from .swing import ForexSwingTradingStrategy
from .scalping import ForexScalpingStrategy
from .breakout import ForexBreakoutStrategy
from .range import ForexRangeTradingStrategy

__all__ = [
    "ForexMomentumStrategy",
    "ForexTrendFollowingStrategy",
    "ForexBreakoutStrategy",
    "ForexDayTradingStrategy",
    "ForexCarryTradeStrategy",
    "ForexSwingTradingStrategy",
    "ForexMomentumStrategy",
    "ForexGridTradingStrategy",
    "ForexRetracementStrategy",
    "ForexPositionTradingStrategy",
    "ForexRangeTradingStrategy",
    "ForexCounterTrendStrategy",
    "ForexScalpingStrategy",
    "ForexSwingTradingStrategy",
    "ForexScalpingStrategy",
    "ForexBreakoutStrategy",
    "ForexRangeTradingStrategy",
]
