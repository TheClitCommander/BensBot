"""
Strategy Factory

This module provides a factory for creating trading strategies
based on strategy type and configuration.
"""

import logging
from typing import Dict, Any, Optional, Type

logger = logging.getLogger(__name__)

# Import available strategies
try:
    from trading_bot.strategies.stocks.momentum import MomentumStrategy
    from trading_bot.strategies.stocks.mean_reversion import MeanReversionStrategy
    from trading_bot.strategies.stocks.trend import MultiTimeframeCorrelationStrategy as TrendFollowingStrategy
    from trading_bot.strategies.stocks.breakout import VolatilityBreakoutStrategy
    STRATEGIES_AVAILABLE = True
except ImportError:
    logger.warning("Some strategy modules could not be imported. Using mock strategies.")
    STRATEGIES_AVAILABLE = False

    # Define mock strategy classes for when real ones aren't available
    class BaseStrategy:
        """Base class for all trading strategies"""
        
        def __init__(self, config=None):
            self.config = config or {}
            logger.info(f"Initialized {self.__class__.__name__}")
            
        def generate_signals(self, data, **kwargs):
            """Generate trading signals"""
            return {"action": "hold", "confidence": 0.5}
        
        @classmethod
        def is_available(cls):
            return True
    
    class MomentumStrategy(BaseStrategy):
        """Mock momentum strategy"""
        pass
    
    class MeanReversionStrategy(BaseStrategy):
        """Mock mean reversion strategy"""
        pass
    
    class TrendFollowingStrategy(BaseStrategy):
        """Mock trend following strategy"""
        pass
    
    class VolatilityBreakoutStrategy(BaseStrategy):
        """Mock volatility breakout strategy"""
        pass


class StrategyFactory:
    """Factory class for creating strategy objects"""
    
    @staticmethod
    def create_strategy(strategy_type: str, config: Optional[Dict[str, Any]] = None):
        """
        Create a strategy object by type
        
        Args:
            strategy_type: Type of strategy to create
            config: Optional configuration dictionary
            
        Returns:
            Strategy object
        """
        config = config or {}
        
        # Create strategy based on type
        if strategy_type.lower() == "momentum":
            return MomentumStrategy("Momentum Strategy", parameters=config)
        elif strategy_type.lower() == "mean_reversion":
            return MeanReversionStrategy("Mean Reversion Strategy", config)
        elif strategy_type.lower() == "trend_following":
            return TrendFollowingStrategy("Trend Following Strategy", config)
        elif strategy_type.lower() == "volatility_breakout":
            return VolatilityBreakoutStrategy("Volatility Breakout Strategy", config)
        else:
            logger.warning(f"Unknown strategy type: {strategy_type}. Using momentum strategy.")
            return MomentumStrategy("Momentum Strategy", parameters=config)
    
    @staticmethod
    def available_strategies():
        """Get names of available strategies"""
        return [
            "momentum",
            "mean_reversion",
            "trend_following",
            "volatility_breakout"
        ] 