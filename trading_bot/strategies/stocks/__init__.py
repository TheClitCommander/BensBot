#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Stocks strategies package.
"""

# Import subpackages
from . import base
from . import trend
from . import momentum
from . import value
from . import growth
from . import dividend
from . import mean_reversion
from . import breakout
from . import technical
from . import fundamental
from . import sentiment
from . import statistical

# Import all strategies
from .trend import StocksTrendStrategy
from .momentum import StocksMomentumStrategy
from .value import StocksValueStrategy
from .growth import StocksGrowthStrategy
from .dividend import StocksDividendStrategy
from .mean_reversion import StocksMean_reversionStrategy
from .breakout import StocksBreakoutStrategy
from .technical import StocksTechnicalStrategy
from .fundamental import StocksFundamentalStrategy
from .sentiment import StocksSentimentStrategy
from .statistical import StocksStatisticalStrategy

__all__ = [
    "StocksBaseStrategy",
        "StocksTrendStrategy",
    "StocksMomentumStrategy",
    "StocksValueStrategy",
    "StocksGrowthStrategy",
    "StocksDividendStrategy",
    "StocksMean_reversionStrategy",
    "StocksBreakoutStrategy",
    "StocksTechnicalStrategy",
    "StocksFundamentalStrategy",
    "StocksSentimentStrategy",
    "StocksStatisticalStrategy",
]
