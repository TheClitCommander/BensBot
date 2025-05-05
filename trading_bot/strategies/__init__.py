#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Trading strategies package.
"""

# Make sure the package is properly defined and has the __path__ attribute
__path__ = __import__('pkgutil').extend_path(__path__, __name__)

# Import all strategy modules
from . import options
from . import crypto
from . import forex
from . import stocks
from . import factory

# Direct import and re-export of StrategyFactory
# This makes it directly importable from trading_bot.strategies
try:
    from .factory.strategy_factory import StrategyFactory
    from .factory.strategy_registry import (
        StrategyRegistry, 
        AssetClass, 
        StrategyType, 
        MarketRegime, 
        TimeFrame
    )
    __all__ = [
        'StrategyFactory',
        'StrategyRegistry',
        'AssetClass',
        'StrategyType',
        'MarketRegime',
        'TimeFrame',
        'options',
        'crypto',
        'forex',
        'stocks',
        'factory'
    ]
except ImportError as e:
    import sys
    import logging
    logging.warning(f"Error importing strategy components: {e}")
    # Create placeholder if import fails
    class StrategyFactory:
        @staticmethod
        def create_strategy(*args, **kwargs):
            return None
    sys.modules[__name__ + '.strategy_factory'] = __import__('types').ModuleType('strategy_factory')
    sys.modules[__name__ + '.strategy_factory'].StrategyFactory = StrategyFactory
